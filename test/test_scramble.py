import sys
sys.path.append('scripts')
from m_prompt import *

test_prompt = mPrompt()
test_prompt.LoadPrompt('test/sakamata-in.txt')
test_prompt.ScrambleOrder(20)
test_prompt.ScrambleReduction(2, 1)
test_prompt.ScrambleWeights(0.5, inIsLora=False)
test_prompt.ScrambleWeights(0.5, inIsLora=False, inLimit=5, inVariance=2, inMinInput=0.7, inMaxInput=None, inMinOutput=0.3, inMaxOutput=1.1)
test_prompt.ScrambleWeights(0.5, inIsLora=True)
test_prompt.Generate()
test_prompt.SavePrompt('test/sakamata-out.txt')
pass
