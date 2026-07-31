"""
LangGraph Supervisor (Main Controller)
----------------------------------------
Wires together all specialist agents into a single graph matching
the architecture diagram:

        START
          |
   +------+------+------+
   |      |             |
 news  financial   technical      (run in parallel)
   |      |             |
   +------+------+------+
          |
        risk                       (fan-in: waits for all three)
          |
      portfolio
          |
       advisor
          |
        report
          |
         END
"""
import logging

from langgraph.graph import END, START, StateGraph

from app.agents.advisor_agent import run_advisor_agent
from app.agents.financial_report_agent import run_financial_report_agent
from app.agents.news_agent import run_news_agent
from app.agents.portfolio_agent import run_portfolio_agent
from app.agents.report_agent import run_report_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.state import ResearchState
from app.agents.technical_agent import run_technical_agent

logger = logging.getLogger(__name__)

_compiled_graph = None


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("news_agent", run_news_agent)
    graph.add_node("financial_report_agent", run_financial_report_agent)
    graph.add_node("technical_agent", run_technical_agent)
    graph.add_node("risk_agent", run_risk_agent)
    graph.add_node("portfolio_agent", run_portfolio_agent)
    graph.add_node("advisor_agent", run_advisor_agent)
    graph.add_node("report_agent", run_report_agent)

    # Fan-out from START to the three independent specialist agents
    graph.add_edge(START, "news_agent")
    graph.add_edge(START, "financial_report_agent")
    graph.add_edge(START, "technical_agent")

    # Fan-in: risk_agent waits until all three predecessors complete
    graph.add_edge("news_agent", "risk_agent")
    graph.add_edge("financial_report_agent", "risk_agent")
    graph.add_edge("technical_agent", "risk_agent")

    # Sequential remainder of the pipeline
    graph.add_edge("risk_agent", "portfolio_agent")
    graph.add_edge("portfolio_agent", "advisor_agent")
    graph.add_edge("advisor_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph.compile()


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_research_pipeline(
    ticker: str,
    uploaded_pdf_path: str | None = None,
    portfolio_holdings: list[dict] | None = None,
) -> ResearchState:
    """Execute the full multi-agent pipeline for a given ticker."""
    graph = get_compiled_graph()
    initial_state: ResearchState = {
        "ticker": ticker.upper(),
        "uploaded_pdf_path": uploaded_pdf_path,
        "portfolio_holdings": portfolio_holdings,
        "errors": [],
    }
    final_state = graph.invoke(initial_state)
    return final_state
