"""Task 14: private MCP server exposing check_loan_application_status via fastmcp.

Run:  python mcp_server.py          -> http://127.0.0.1:8001/mcp  (streamable HTTP)
(Port 8001 so it doesn't clash with the FastAPI app on 8000; override with MCP_PORT.)
"""
import os

from fastmcp import FastMCP

from app.loan_tool import check_loan_application_status as _check

mcp = FastMCP("cred-loan-tools")


@mcp.tool()
def check_loan_application_status(record_id: str) -> dict:
    """Look up a Cred loan application by record ID (e.g. "LA-1005").

    Returns the application's status, loan_amount_inr and a designed
    escalation_score in [0, 1] = 0.5*flagged_for_fraud_review + 0.5*(days_since_created/30).
    Escalation is recommended when the score is >= 0.70. If the record does not
    exist, found is false and an error message is returned.
    """
    return _check(record_id)


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=int(os.getenv("MCP_PORT", "8001")), path="/mcp")
