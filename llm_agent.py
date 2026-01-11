from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re
import actions

def get_llm():
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0.6)

def get_llm_response(query: str, is_json=False) -> str:
    llm = get_llm()
    
    if is_json:
        # Prompt for pure JSON output
        system_instruction = "You are a software architect. Output ONLY raw JSON code. No text outside the JSON."
    else:
        # Human personality prompt
        system_instruction = """
        You are Jarvis, a friendly and concise AI assistant.
        1. Talk like a real person. Keep it short (1-2 sentences).
        2. Do NOT provide lists, robotic references, or Google-style explanations.
        3. For computer tasks, use: [COMMAND: action_name arguments].
        Actions: open_website, open_app, open_explorer, create_project, delete_file.
        """

    prompt = ChatPromptTemplate.from_messages([("system", system_instruction), ("user", "{query}")])
    chain = prompt | llm
    try:
        res = chain.invoke({"query": query})
        return res.content
    except:
        return "I am having some trouble thinking right now."

def process_command(text: str):
    match = re.search(r"\[COMMAND: (.*?)\]", text)
    if not match: return False

    cmd_line = match.group(1).strip().split(maxsplit=1)
    name = cmd_line[0]
    args = cmd_line[1] if len(cmd_line) > 1 else None

    mapping = {
        "open_website": actions.open_website,
        "open_app": actions.open_app,
        "open_explorer": actions.open_explorer,
        "create_project": actions.create_coding_project,
        "delete_file": actions.delete_file_safely
    }

    if name in mapping:
        try:
            if args: mapping[name](args)
            else: mapping[name]()
            return True
        except:
            return True
    return False