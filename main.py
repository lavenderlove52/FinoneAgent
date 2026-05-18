from backend.llm_client import LLMClient


def test_connection() -> None:
    client = LLMClient()
    message = client.complete(
        [
            {
                "role": "user",
                "content": "Tell me, why is the sky blue?",
            },
        ]
    )
    print(f"Assistant: {message}")


if __name__ == "__main__":
    test_connection()
