import asyncio

from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console

from Agents.core_agents import create_agents


async def main():
    # Create all agents
    user_proxy, idea_enhancer, market_questionnaire, market_agent, tech_solution, ba_agent, estimator_agent, supervisor, model_client = create_agents()

    # Set up the team chat
    team = SelectorGroupChat(
        participants=[user_proxy, supervisor, idea_enhancer, market_questionnaire, tech_solution, estimator_agent, ba_agent, market_agent],
        model_client=model_client,
        allow_repeated_speaker=True,
        termination_condition=MaxMessageTermination(50) | TextMentionTermination("TERMINATE")
    )

    try:
        task = input('Enter your idea here (type your idea and press Enter): ')
        stream = team.run_stream(task=task)
        await Console(stream)
    except EOFError:
        print("ERROR: Cannot read input in this environment.")
        print("Please run this script in an interactive terminal.")
        print("Make sure you have configured your API keys in a .env file first.")
        return

if __name__ == "__main__":
    asyncio.run(main())