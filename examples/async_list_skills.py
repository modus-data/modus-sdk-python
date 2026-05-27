"""
Example: listing skills using the async client.

Run with:
    export MODUS_API_KEY=modus_xxx
    python examples/async_list_skills.py
"""
import asyncio
import modus


async def main() -> None:
    async with modus.AsyncModus() as client:
        print("=== Skills (async) ===")
        page = await client.skills.list()
        skills = []
        async for skill in page.auto_paging_iter():
            skills.append(skill)
            status = "active" if skill.is_active else "draft"
            print(f"  [{status}] {skill.name}  (id={skill.id})")

        print(f"\nTotal: {len(skills)} skill(s).")


if __name__ == "__main__":
    asyncio.run(main())
