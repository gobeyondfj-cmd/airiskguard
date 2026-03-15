"""Flask example with airiskguard middleware."""

from flask import Flask, jsonify, request

from airiskguard import RiskGuard
from airiskguard.integrations.flask import add_risk_guard

app = Flask(__name__)

# One-line integration
add_risk_guard(app, config={"enabled_checkers": ["fraud", "compliance", "security"]})

guard = RiskGuard()


@app.route("/process-payment", methods=["POST"])
def process_payment():
    data = request.get_json()

    report = guard.evaluate_sync(
        input_data=data,
        output_data={"status": "processing"},
        model_id="payment-v1",
        checks=["fraud", "compliance"],
    )

    if report.blocked:
        return jsonify({
            "error": "Transaction blocked by risk assessment",
            "risk_level": report.overall_risk.value,
        }), 403

    return jsonify({
        "status": "approved",
        "risk_score": report.overall_score,
        "risk_level": report.overall_risk.value,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
