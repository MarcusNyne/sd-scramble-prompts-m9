import re
import random

class mPrompt:

    sLineSplit = 120

    def __init__(self, inSeed=None, inPrompt=None) -> None:
        self.seed = inSeed
        self.Reset()
        if inPrompt is not None:
            self.__init_prompt(inPrompt)

    def LoadPrompt(self, inFilePath:str) -> None:
        self.Reset()
        try:
            f = open(inFilePath, "rt")
            lines = f.readlines()
            f.close()
            self.__init_prompt("\n".join(lines))

        except:
            return False

        return True

    def SavePrompt(self, inFilePath:str) -> None:
        if type(self.p_output) is not str:
            return False

        try:
            f = open(inFilePath, "wt")
            f.write(self.p_output)
            f.close()

        except:
            return False

        return True

    def Reset(self):
        self.p_string = ""
        self.p_prompts = []
        self.__reset_generation()

    def ScrambleOrder(self, inLimit=None, inVariance:int=None):
        # limit None scrambles the entire list
        # if limit is specified, only a limited number are reordered
        if inLimit is None or inLimit==0:
            random.seed(self.seed)
            random.shuffle(self.p_prompts)
        elif type(inLimit) is int:
            if inVariance is not None:
                random.seed(self.seed)
                inLimit += random.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)

            ln = len(self.p_prompts)
            pmap = list(range(ln))
            while inLimit>0 and ln>1:
                r1=0
                r2=0
                while r1==r2:
                    random.seed(self.seed)
                    r1 = random.randrange(0, ln)
                    random.seed(self.seed)
                    r2 = random.randrange(0, ln)
                a = pmap[r1]
                pmap[r1]=pmap[r2]
                pmap[r2] = a
                inLimit-=1

            tks = []
            for r in range(ln):
                tks.append(self.p_prompts[pmap[r]])
            self.p_prompts = tks

    def ScrambleWeights(self, inRange:float, inIsLora=False, inLimit=None, inVariance=None, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        ln = len(self.p_prompts)

        pmap = []
        for x in range(ln):
            if inIsLora is False and 'lora' not in self.p_prompts[x]:
                pmap.append(x)
            elif inIsLora is True and 'lora' in self.p_prompts[x]:
                pmap.append(x)

        ln = len(pmap)

        random.seed(self.seed)
        random.shuffle(pmap)
        if inLimit is not None:
            inLimit = min(inLimit, ln)
            if inVariance is not None:
                random.seed(self.seed)
                inLimit += random.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)

            pmap = pmap[:inLimit]

        for p in pmap:
            weight = self.p_prompts[p]['weight'] if 'weight' in self.p_prompts[p] else 1
            self.p_prompts[p]['weight'] = self.__modify_weight(weight, inRange, inMinInput=inMinInput, inMaxInput=inMaxInput, inMinOutput=inMinOutput, inMaxOutput=inMaxOutput)

    def TweakWeights(self, inKeywords:str, inRange:float, inLoraRange:float, inMaxOutput:float=None):
        keywords = []
        for kw in inKeywords.split(','):
            kw = kw.lower().strip()
            if kw!="":
                keywords.append(kw)

        ln = len(self.p_prompts)
        for x in range(ln):
            if self.__match(keywords, self.p_prompts[x]['token']):
                weight = self.p_prompts[x]['weight'] if 'weight' in self.p_prompts[x] else 1
                r = inLoraRange if 'lora' in self.p_prompts[x] else inRange
                self.p_prompts[x]['weight'] = self.__modify_weight(weight, r, inMinOutput=0, inMaxOutput=inMaxOutput)

    def __match(self, inKeywords:list, inString:str):
        inString = inString.lower()
        for kw in inKeywords:
            if kw in inString:
                return True
        return False

    def __modify_weight(self, inWeight:float, inRange:float, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        if (inMinInput is not None and inWeight<inMinInput) or (inMaxInput is not None and inWeight>inMaxInput):
            return inWeight

        random.seed(self.seed)
        mod = (random.random() * inRange * 2)-inRange
        if inMinOutput is not None and (inWeight+mod) < inMinOutput:
            return inWeight
        if inMaxOutput is not None and (inWeight+mod) > inMaxOutput:
            return inWeight
        return inWeight+mod

    def ScrambleReduction(self, inTarget:int, inRange:int=None, inKeepTokens:str=None):
        # target is number to eliminiate
        # range will randomize it as +/-
        # will not eliminate loras
        # will not eliminate tokens where there is a substring match on inKeepTokens
        if inTarget is None:
            return
            
        keep_tokens = []
        if inKeepTokens is not None:
            for tk in inKeepTokens.split(','):
                tk = tk.lower().strip()
                if tk!= "":
                    keep_tokens.append(tk)

        ln = len(self.p_prompts)

        pmap = []
        for x in range(ln):
            if 'lora' not in self.p_prompts[x]:
                pmap.append(x)

        random.seed(self.seed)
        random.shuffle(pmap)

        if inRange is not None:
            random.seed(self.seed)
            inTarget += random.randint(1, inRange*2) - inRange
        inTarget = min(max(inTarget, 1), len(pmap)-1)

        pmap = pmap[:inTarget]

        tks = []
        for x in range(ln):
            keep = False
            if x in pmap:
                for kt in keep_tokens:
                    if kt in self.p_prompts[x]['token'].lower():
                        keep = True
                        break
            if keep or x not in pmap:
                tks.append(self.p_prompts[x])

        self.p_prompts = tks

    def Generate(self):
        self.__reset_generation()
        self.p_output = ""
        llen = 0
        for p in self.p_prompts:
            tk = p['token']
            pcnt = 0
            weight = None
            if 'weight' in p:
                weight = p['weight']
                if 'lora' not in p:
                    paren = self.__calc_paren(weight)
                    if paren[0]>0 and paren[1] is not None:
                        pcnt = paren[0]
                        weight = paren[1]
            if weight is not None and weight!=1:
                tk += ":{w:.3}".format(w=weight)
            if pcnt>0:
                tk = ("("*pcnt)+tk+(")"*pcnt)
            if 'lora' in p:
                tk = "<"+tk+">"
            if llen>0:
                if llen+len(tk)>mPrompt.sLineSplit:
                    self.p_output += "\n"
                    llen = 0
                else:
                    self.p_output += ","
            self.p_output += tk
            llen += len(tk)
        return self.p_output

    def TestParse(self, inPrompt:str):
        self.__init_prompt(inPrompt)
        for prompt in self.p_prompts:
            print(prompt)

    def __calc_paren(self, inWeight:float):
        # returns a tuple as (parens, weight)
        if inWeight == 1:
            return (0, None)
        
        ideal_parens = 0
        ideal_weight = inWeight
        ideal_wlen = self.__w_len(inWeight)

        for pfactor in range(5):
            factor = 1.05 ** pfactor
            wlen = self.__w_len(inWeight/factor)
            if wlen < 4 and wlen < ideal_wlen:
                ideal_parens = pfactor
                ideal_weight = inWeight/factor
                ideal_wlen = wlen
                if ideal_weight==1.0:
                    break

        return (ideal_parens, ideal_weight)

    def __w_len(self, inWeight:float):
        if (inWeight % 1) == 0:
            return len(str(int(inWeight)))
        return len(str(inWeight))

    def __reset_generation(self):
        self.p_output = None

    def __init_prompt(self, inPrompt:str):
        self.p_string = inPrompt
        p = inPrompt.replace("\n", ",").replace("<", ",<").replace(">", ">,")
        lst = re.split(",(?![^\(]*\))", p)
        tks = []
        for l in lst:
            tk = self.__make_token(l)
            if tk is not None:
                tks.append(tk)
        self.p_prompts = tks

    def __make_token(self, inPrompt:str):
        inPrompt = inPrompt.strip()
        if inPrompt=="":
            return None
        inPrompt = inPrompt.replace("\\(", "@@@").replace("\\)", "###")
        pcnt = inPrompt.count("(")
        inPrompt = inPrompt.replace("(", "").replace(")", "")
        lcnt = inPrompt.count("<")
        inPrompt = inPrompt.replace("<", "").replace(">", "")
        weight = 1
        pw = inPrompt.split(":")
        if len(pw)>1:
            try:
                weight = (float)(pw[-1])
                inPrompt = ":".join(pw[:len(pw)-1]).strip()
            except:
                pass

        while pcnt>0:
            weight = weight * 1.05;
            pcnt -= 1

        if weight==0 or inPrompt=="":
            return None

        inPrompt = inPrompt.replace("@@@", "\\(").replace("###", "\\)")
        
        tk = {'token':inPrompt}
        if weight is not None and weight!=1:
            tk['weight'] = weight
        if lcnt>0:
            tk['lora'] = True

        return tk
