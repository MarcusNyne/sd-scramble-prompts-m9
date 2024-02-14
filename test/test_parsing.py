import sys
sys.path.append('scripts')
from m_prompt import *

def test(inPrompt):
    print (inPrompt)
    test_prompt = mPrompt()
    test_prompt.TestParse(inPrompt)

test ("one,two,three")
test ("on(e,t)wo,three")
test ("<lora:arms_v10:.2><lora:fun:0.4>something :1.1<lora:third:0.6>")