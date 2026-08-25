"""Giám sát Data Drift cho mô hình Iris.

Ưu tiên dùng Evidently (chuẩn ngành) để sinh báo cáo HTML + JSON.
Nếu Evidently không cài được/không tương thích môi trường, tự động
fallback sang kiểm định Kolmogorov-Smirnov (KS) từng feature — cùng
thuật toán mà Evidently dùng bên trong cho dữ liệu số.

Kết quả:
  - reports/drift_report.html  : báo cáo chi tiết
  - reports/drift_summary.json : tóm tắt trạng thái từng feature
  - Exit code 1 nếu phát hiện drift (để CI/cron kích hoạt retrain)
"""
import argparse
import json
import os
import sys
import urllib.request

# Đảm bảo in được tiếng Việt trên Windows console (cp1252)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

DEFAULT_REFERENCE = os.path.join("artifacts", "reference_data.csv")
REPORT_DIR = "reports"
KS_ALPHA = 0.05  # p-value < 0.05 => hai phân phối khác biệt đáng kể => drift


def parse_args():
    parser = argparse.ArgumentParser(description="Data drift monitoring")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE, help="CSV dữ liệu tham chiếu (lúc train)")
    parser.add_argument("--current", default=None, help="CSV dữ liệu thực tế từ production (tuỳ chọn)")
    parser.add_argument(
        "--shift-strength",
        type=float,
        default=0.8,
        help="Mức độ dịch chuyển mô phỏng khi không có dữ liệu production (0=không drift)",
    )
    parser.add_argument("--no-exit-on-drift", action="store_true", help="Không trả exit code 1 khi có drift")
    return parser.parse_args()


def load_data(args):
    if not os.path.exists(args.reference):
        print(f"❌ Không tìm thấy reference data: {args.reference}. Hãy chạy train.py trước.")
        sys.exit(2)
    reference = pd.read_csv(args.reference)

    if args.current:
        current = pd.read_csv(args.current)
    else:
        # Mô phỏng lô dữ liệu production bị dịch chuyển: mean += shift_strength * std
        rng = np.random.default_rng(42)
        current = reference.copy()
        for col in reference.columns:
            shift = args.shift_strength * float(reference[col].std())
            current[col] = reference[col] + shift + rng.normal(0, reference[col].std() * 0.05, len(reference))
    return reference, current


# ----------------------- Phương án 1: Evidently -----------------------

def run_evidently(reference, current):
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)
    summary = report.as_dict()

    drifted_columns = {}
    dataset_drift = False
    for metric in summary.get("metrics", []):
        result = metric.get("result", {})
        by_columns = result.get("drift_by_columns")
        if isinstance(by_columns, dict):
            for column, info in by_columns.items():
                drifted_columns[column] = bool(info.get("drift_detected"))
        if "dataset_drift" in result:
            dataset_drift = bool(result["dataset_drift"])

    engine = "evidently"
    html_path = os.path.join(REPORT_DIR, "drift_report.html")
    try:
        report.save_html(html_path)
    except Exception as exc:  # noqa: BLE001 - báo cáo HTML là tiện ích, không chặn luồng chính
        print(f"⚠️ Không lưu được HTML report: {exc}")
    return dataset_drift, drifted_columns, engine, html_path


# ------------------- Phương án 2: KS-test fallback -------------------

def run_ks(reference, current):
    """Kiểm định Kolmogorov-Smirnov từng cột số (p < KS_ALPHA => drift)."""
    drifted_columns = {}
    for column in reference.columns:
        statistic, p_value = ks_2samp(
            reference[column].to_numpy(), current[column].to_numpy()
        )
        drifted_columns[column] = bool(p_value < KS_ALPHA)
        print(f"   [{column}] KS statistic={statistic:.4f}, p-value={p_value:.4f}")
    dataset_drift = any(drifted_columns.values())
    engine = "ks-fallback"
    return dataset_drift, drifted_columns, engine, None


# ----------------------------- Alerting -----------------------------

def send_alert(message: str):
    """Gửi cảnh báo tới webhook (Slack/Teams/...) nếu cấu hình biến môi trường."""
    webhook_url = os.environ.get("ALERT_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        payload = json.dumps({"text": message}).encode()
        request = urllib.request.Request(
            webhook_url, data=payload, headers={"Content-Type": "application/json"}
        )
        # URL lấy từ biến môi trường do vận hành kiểm soát, không phải input người dùng
        urllib.request.urlopen(request, timeout=5)  # nosec B310
        print("📣 Đã gửi alert tới webhook.")
    except Exception as exc:  # noqa: BLE001 - alert lỗi không được làm sập job giám sát
        print(f"⚠️ Gửi alert thất bại: {exc}")


def main():
    args = parse_args()
    reference, current = load_data(args)
    os.makedirs(REPORT_DIR, exist_ok=True)

    print("=== GIÁM SÁT DATA DRIFT ===")
    print(f"Reference: {len(reference)} dòng | Current: {len(current)} dòng\n")

    try:
        dataset_drift, drifted, engine, html_path = run_evidently(reference, current)
    except Exception as exc:  # noqa: BLE001
        print(f"ℹ️ Evidently không khả dụng ({exc}). Chuyển sang KS-test fallback.\n")
        dataset_drift, drifted, engine, html_path = run_ks(reference, current)

    for column, has_drift in drifted.items():
        status = "🚨 DRIFT" if has_drift else "✅ ổn định"
        print(f" - {column:<18}: {status}")
    print(f"\nEngine: {engine} | Dataset drift: {'CÓ' if dataset_drift else 'KHÔNG'}")

    summary = {
        "dataset_drift": dataset_drift,
        "engine": engine,
        "drifted_columns": drifted,
        "reference_rows": len(reference),
        "current_rows": len(current),
    }
    with open(os.path.join(REPORT_DIR, "drift_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if dataset_drift:
        columns_text = ", ".join(c for c, d in drifted.items() if d)
        message = f"[mlops-lab1] 🚨 Data drift phát hiện trên: {columns_text}. Cân nhắc retrain."
        print(f"\n{message}")
        if html_path:
            print(f"Báo cáo chi tiết: {html_path}")
        send_alert(message)
        if not args.no_exit_on_drift:
            sys.exit(1)
    else:
        print("\n✅ Dữ liệu ổn định, không cần retrain.")


if __name__ == "__main__":
    main()
