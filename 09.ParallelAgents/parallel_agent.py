import sys
import asyncio
from openai import AsyncOpenAI
from specialist_agent import AsyncSpecialistAgent

sys.path.append("..")
from config import AgentConfig


class ParallelAgentSystem:
    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.client = AsyncOpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
        )
        self.file_researcher = AsyncSpecialistAgent(
            name="File Researcher",
            system_prompt=(
                "You inspect project files and extract relevant facts. "
                "Return concise factual findings."
            ),
            model=self.model,
            client=self.client,
            tool_names=[
                "read_file",
                "list_files",
            ],
        )

        self.memory_researcher = AsyncSpecialistAgent(
            name="Memory Researcher",
            system_prompt=(
                "You search long-term memory "
                "for information relevant to "
                "the task. Return only relevant facts."
            ),
            model=self.model,
            client=self.client,
            tool_names=[
                "search_memory",
            ],
        )

        self.independent_reviewer = AsyncSpecialistAgent(
            name="Independent Reviewer",
            system_prompt=(
                "You independently analyze the "
                "user's request and identify what "
                "must be verified, calculated, or "
                "checked. Do not invent facts."
            ),
            model=self.model,
            client=self.client,
            tool_names=[],
        )

    async def fan_out(self, user_input: str) -> list[str]:
        results = await asyncio.gather(
            self.file_researcher.run(user_input),
            self.memory_researcher.run(user_input),
            self.independent_reviewer.run(user_input),
            return_exceptions=True
        )

        clean_results = []

        for result in results:

            if isinstance(
                    result,
                    Exception,
            ):
                clean_results.append(
                    f"Agent failed: {result}"
                )

            else:
                clean_results.append(
                    result
                )

        return clean_results

    async def synthesize(self, user_input: str, results: list[str], ) -> str:
        combined = "\n\n".join(
            f"Agent {i + 1} result:\n{result}" for i, result in enumerate(results)
        )

        print(combined)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a synthesis agent. "
                    "Combine the findings from multiple "
                    "specialist agents into one accurate "
                    "answer. Resolve conflicts carefully. "
                    "Do not invent missing facts."
                ),
            },
            {
                "role": "user",
                "content": f"""
    Original request:
    {user_input}

    Specialist results:
    {combined}

    Produce the final answer.
    """.strip(),
            },
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            reasoning_effort="none")

        return response.choices[0].message.content or ""

    async def run(self, user_input: str, ) -> str:
        print()
        print("=" * 60)
        print("FAN-OUT")
        print("=" * 60)

        results = await self.fan_out(user_input)

        print()
        print("=" * 60)
        print("FAN-IN")
        print("=" * 60)

        final_answer = await self.synthesize(user_input, results, )

        print()
        print("=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)

        print(final_answer)

        return final_answer
