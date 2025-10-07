from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from Prompts.idea_enhancer import idea_enhancer_prompt
from Prompts.technical_solutioning import technical_solutioning_prompt
from Templates.brd_template import brd_template
from Templates.srs_template import srs_template
from Templates.frd_template import frd_template
from Templates.sow_template import sow_template
from Templates.rfp_template import rfp_template
from Sample_output.market_research import market_research
from .search_tools import g4o_search_fn, initialize_client
from Sample_output.team_structure import team_structure
from Sample_output.tech_stack import tech_stack
from Sample_output.timeline import timeline
from Sample_output.budget import budget
from config.model_config import config


def create_agents():
    # Initialize the OpenAI client for search tools
    initialize_client(config.get_api_key())
    model_client = config.get_model_client()

    user_proxy = UserProxyAgent(
        name="User",
        input_func=input,
        description="Captures user input and provides feedback. It is called after each agent response no matter who is the agent."
    )

    idea_enhancer = AssistantAgent(
        name="IdeaEnhancer",
        model_client=model_client,
        system_message=f"{idea_enhancer_prompt}",
        description="A creative AI agent that transforms vague ideas into polished product concepts, complete with a name, description, key features, and next-step suggestions. Also helps the user in refining the project idea and answering queries/followups."
    )

    market_questionnaire = AssistantAgent(
        name="MarketQuestionnaire",
        model_client=model_client,
        description="Turns a startup idea into search queries and extracts details.",
        system_message="""
        You are MarketQuestionnaire.
        1) Produce 6–12 short queries (include 'Comprehensive Market Research' and 'Deeper Research' in two).
        2) For each query, call g4o_search_tool(query, search_context_size="high", country="IN") to get recent, cited results.
        3) For top URLs, call extract_page_text(url) and include in depth analysis with citations.
        Output: numbered queries, then per-query findings + extracts.
        """,
        tools=[g4o_search_fn],
        max_tool_iterations=30,
    )

    market_agent = AssistantAgent(
        name="MarketResearcher",
        model_client=model_client,
        description="Runs after the completion of MarketQuestionnnaire and provides competitors, market size, positioning, trends based on the finalised idea based on the latest context.",
        system_message="""### INSTRUCTION ###
        You are a senior market research analyst with deep cross-industry expertise. Your task is to perform an in-depth market research analysis of a specific business idea based on the context already provided to you about the market scenarios. 
        Format your response exactly according to the market_research template.
        """
    )

    tech_solution = AssistantAgent(
        name="TechnicalSolutioning",
        model_client=model_client,
        description="Tells the user about what kind of Tech stack needs to be used based on the idea and market research.",
        system_message=f"{technical_solutioning_prompt}"
    )

    ba_agent = AssistantAgent(
        name="BusinessAnalyst",
        model_client=model_client,
        description="Runs after the user is happy with the Market Research. It Generates business documents (BRD, SRS, FRD, SOW, RFP) based on the finalized idea and estimates.",
        system_message=f"""
        INSTRUCTION
        You are a professional Business Analyst AI assistant.

        Your job is to generate in depth and detailed business documentation based on a finalized product idea and technical estimates. Use a minimum of 5 lines per paragraph and use the context to give out the best and professional grade content. Leave the date as [Today's date]. 

        Strictly do not generate a document till the user asks for it explicitly, Ask clarification questions (Strictly only 1 question at a time so the user doesn't get overwhelmed) to the user regarding what document he/she needs. You can ask a maximum of 3 questions. 
        All the documents must be generated in simple Markdown format. 

        Document Types You Can Generate (ONE at a time):
        BRD- Business Requirements Document
        SRS- Software Requirements Specification
        FRD- Functional Requirements Document
        SOW-  Statement of Work
        RFP- Request for Proposal

        Templates (Use EXACTLY these formats):
        BRD Template - 
        {brd_template}
        SRS Template
        {srs_template}
        FRD Template
        {frd_template}
        SOW Template
        {sow_template}
        RFP Template
        {rfp_template}

        Operating Logic (You MUST follow this loop):
        WAIT for the user to request a specific document out of BRD, SRS, FRD, SOW, or RFP.

        If ambiguous (e.g., "make me something") or not specified a type of document yet, ask:
        "Which document would you like me to generate: BRD, SRS, FRD, SOW, or RFP?"

        Only generate one document per request and the document should be long and extensive, try to incorporate as many things from the idea as possible. 
        Strictly do not move onto the Go to market agent until the user specifically asks for it. 

        After each document, ask:
        "Would you like me to generate another document (BRD, SRS, FRD, SOW, RFP), or move towards Go-to-Market Planning?" and call the User agent everytime. 
        """
    )

    estimator_agent = AssistantAgent(
        name="estimator_agent",
        model_client=model_client,
        description="""Runs only when Provides cost, timeline, tech stack, and team composition estimates based on a finalized business or product idea.""",
        system_message=f"""You are a startup estimator AI. Only proceed when the user explicitly confirms the idea is finalized.

        When given a finalized product idea, your job is to return an estimation of:
        1) Budget in INR- Give a budget breakdown as well for each component like (in the form of a table.):-
        #Sample Output
        {budget}

        2) Development timeline in weeks - The timeline should also include a breakdown of all the things that need to be done with respect to the time required for each, always keep it well detailed. 
        #Sample Output
        {timeline}

        3) Suggested tech stack (frontend, backend, DB, tools)
        #Sample Output- 
        {tech_stack}

        4) Suggested team structure (e.g., 1 frontend dev, 1 backend dev, 1 designer)
        #Sample output- 
        {team_structure} - Do note to always provide the team structure in the provided format only. 

        Note- Strictly use whole numbers for the entire process and do not under any circumstance give numbers as decimal.

        Be concise and clear. Use markdown format. After providing the estimates, ask the user if they would like to make any iterations with the provided requirements and call the user agent."""
    )

    supervisor = AssistantAgent(
        name='WorkflowRouter',
        model_client=model_client,
        system_message="""### Instruction###
         You are **WorkflowRouter**, a silent orchestrator that Strictly never prints text to the user and never takes user input just calls the next agent that it feels fit. your task is to manage the workflow below and after each agent you have to call the user agent to get the responses, this is non negotiable except for  MarketQuestionnaire agent where you can call Market Researcher right after the market questionnaire. 

         #### Agent roster (fixed order)
         1. IdeaEnhancer         -  Works on ideas, features, product. Calls the MarketQuestionnaire once the user says specifically to call it or is happy with the final idea. 
         2. MarketQuestionnaire. - Formulates questions based on Finalised product idea.
         3. MarketResearcher     - Searches the web based on Questions provided by MarketQuestionnaire.
         4. TechnicalSolutioning - gives the technical specifications based on the Market research and the finalised idea. 
         5. BusinessAnalyst      -  After Market research, it generates the documents like (BRD, SRS, FRD, SOW, or RFP)
         6. EstimatorAgent       -   After the Go to Market Strategy is finalised, the EstimatorAgent provides the estimates for the product(if any changes are made to the budget or any estimations- also check in with the IdeaEnhancer to confirm the Idea/Set of features.)

         #### Routing rules
        1)After any model (non-user) responds, inspect the latest user message.
        If the user expresses satisfaction, ask:  
        "Would you like to move to the next phase: [Phase Name]?"  
        Wait for the user's response.  
        - If the user agrees, call the next agent.  
        - If not, stay in the current phase or ask for clarification.         
         3. If the user requests changes or clarification, **re-invoke the same agent**.  
         4. If the user asks for a market analysis at any time, jump to **MarketQuestionnaire** and then directly to **MarketResearcher**; resume the fixed order afterwards and do not invoke 2 agents in parallel if there is no UserProxyAgent in between except the use case discussed above.  
         5. When the final recommendation is produced, call **TERMINATE**.  
         6. At no time should WorkflowRouter send messages, logs or questions to the user—its only visible effect is invoking the next agent.
         7. If the user asks to do a specific task or call a specific agent then the agent that is responsible for that particular task should be called and after that the flow should remain the same as per the past sequence that was broken.
         ### End of Instruction###
         """,
        description="Routes workflow between agents based on current phase and user readiness to proceed",
    )

    return user_proxy, idea_enhancer, market_questionnaire, market_agent, tech_solution, ba_agent, estimator_agent, supervisor, model_client