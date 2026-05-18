from __future__ import annotations

import argparse

from backend.agents.deep_research import DeepResearchAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="FinoneAgent MVP CLI")
    parser.add_argument("query", help="User question")
    parser.add_argument(
        "--retrieve-only",
        action="store_true",
        help="Only run local retrieval; does not call the remote model.",
    )
    args = parser.parse_args()

    agent = DeepResearchAgent()
    if args.retrieve_only:
        for result in agent.retrieve(args.query):
            print(
                f"[{result.source_type}:{result.source_id}] "
                f"{result.title} score={result.score:.2f}"
            )
            print(result.content)
            print()
        return

    for token in agent.ask_stream(args.query):
        print(token, end="", flush=True)
    print()


if __name__ == "__main__":
    main()

