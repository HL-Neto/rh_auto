from API.api import app 
from MODULLES.module import pdfRead
from LLM.llm  import llm_process, command_process




if __name__ == "__main__": app.run( host="0.0.0.0", port=5000, debug=True, use_reloader = False)