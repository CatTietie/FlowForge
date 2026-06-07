from fastapi import APIRouter, HTTPException

from schemas.schemas import SimulateRequest, SimulateResponse
from engine.simulator import ProcessSimulator
from engine.process_engine import ProcessEngineError

router = APIRouter(prefix="/api/processes", tags=["simulation"])


@router.post("/simulate", response_model=SimulateResponse)
def simulate_process(req: SimulateRequest):
    definition = req.definition.model_dump()
    decisions = [d.model_dump() for d in req.decisions]

    try:
        simulator = ProcessSimulator(
            definition=definition,
            form_data=req.form_data,
            decisions=decisions,
            auto_approve=req.auto_approve,
        )
        result = simulator.run()
    except ProcessEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
