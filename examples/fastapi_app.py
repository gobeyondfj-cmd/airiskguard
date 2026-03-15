"""FastAPI example with airiskguard middleware."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from airiskguard import RiskGuard
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI(title="AI Payment Service")

# One-line integration
add_risk_guard(app, config={"enabled_checkers": ["fraud", "compliance", "security"]})

# Or use the guard directly for more control
guard = RiskGuard()


@app.on_event("startup")
async def startup() -> None:
    await guard.initialize()
    await guard.registry.register(
        name="payment-classifier", version="2.0",
        owner="ml-team", model_id="payment-v2",
    )


@app.post("/process-payment")
async def process_payment(request: Request) -> JSONResponse:
    data = await request.json()

    report = await guard.evaluate(
        input_data=data,
        output_data={"status": "processing"},
        model_id="payment-v2",
        checks=["fraud", "compliance"],
    )

    if report.blocked:
        return JSONResponse(
            status_code=403,
            content={"error": "Transaction blocked by risk assessment",
                     "risk_level": report.overall_risk.value},
        )

    return JSONResponse(content={
        "status": "approved",
        "risk_score": report.overall_score,
        "risk_level": report.overall_risk.value,
    })


@app.get("/risk-dashboard")
async def dashboard() -> JSONResponse:
    summary = await guard.dashboard.get_summary()
    return JSONResponse(content=summary)
