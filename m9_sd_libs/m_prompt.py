import re
import random

class mPrompt:

    sLineSplit = 120

    def __init__(self, inSeed=None, inPrompt=None) -> None:
        self.seed = inSeed
        self.Reset()
        if inPrompt is not None:
            self.__init_prompt(inPrompt)

    def CountTokens(self, inCategory:str=None):
        if inCategory is None:
            return len(self.p_prompts)
        
        cnt = 0
        for p in self.p_prompts:
            match inCategory:
                case 'prompt':
                    if 'lora' not in p:
                        cnt += 1
                case 'lora':
                    if 'lora' in p:
                        cnt += 1

        return cnt

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

    def SavePrompt(self, inFilePath:str, inLog:bool=False) -> None:
        if type(self.p_output) is not str:
            return False

        try:
            f = open(inFilePath, "wt")
            f.write(self.p_output)
            if inLog is True:
                f.write("\n\n")
                for l in self.p_log:
                    if not l.startswith("="):
                        f.write("\t")
                    f.write(l+"\n")
            f.close()

        except:
            return False

        return True

    def Reset(self):
        self.p_string = ""
        self.p_prompts = []
        self.p_log = []
        self.__reset_generation()

    def ScrambleOrder(self, inLimit=None, inVariance:int=None):
        # limit None scrambles the entire list
        # if limit is specified, only a limited number are reordered
        if inLimit==0:
            return
        if inLimit is None:
            random.seed(self.seed)
            random.shuffle(self.p_prompts)
            self.__log_header("All prompts reordered")
        elif type(inLimit) is int:
            if inVariance is not None:
                random.seed(self.seed)
                inLimit += random.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)

            ln = len(self.p_prompts)
            pmap = list(range(ln))
            reordered = []
            while inLimit>0 and len(reordered)<ln:
                r1=0
                r2=0
                try_cnt = 0
                while try_cnt<ln*3 and (r1==r2 or pmap[r1] in reordered):
                    random.seed(self.seed)
                    r1 = random.randrange(0, ln)
                    random.seed(self.seed)
                    r2 = random.randrange(0, ln)
                    try_cnt += 1
                if try_cnt>=ln*3:
                    break

                reordered.append(pmap[r1])

                pmap = self.__shift(pmap, r1, r2)
                inLimit -= 1

            cnt = 0
            for r in range(len(pmap)):
                if pmap[r] in reordered and pmap[r]!=r:
                    cnt += 1

            if cnt>0:
                self.__log_header("{} prompts reordered".format(cnt))

                for r in range(len(pmap)):
                    if pmap[r] in reordered and pmap[r]!=r:
                        if r<pmap[r]:
                            self.__log_entry(self.p_prompts[r]['token'], "Moved up by {cnt}".format(cnt=pmap[r]-r))
                        else:
                            self.__log_entry(self.p_prompts[r]['token'], "Moved down by {cnt}".format(cnt=r-pmap[r]))

                tks = []
                for r in range(ln):
                    tks.append(self.p_prompts[pmap[r]])
                self.p_prompts = tks

    def ScrambleWeights(self, inRange:float, inIsLora=False, inLimit=None, inVariance=None, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        if inLimit is None:
            return
        
        ln = len(self.p_prompts)

        pmap = []
        for x in range(ln):
            if inIsLora is False and 'lora' not in self.p_prompts[x]:
                pmap.append(x)
            elif inIsLora is True and 'lora' in self.p_prompts[x]:
                pmap.append(x)

        ln = len(pmap)
        if ln==0:
            return

        target = "prompt" if inIsLora is False else "lora"
        random.seed(self.seed)
        random.shuffle(pmap)
        if inLimit is None:
            self.__log_header("All {target} weights changed ({range:0.1f})".format(target=target, range=inRange))
        else:
            inLimit = min(inLimit, ln)
            if inVariance is not None:
                random.seed(self.seed)
                inLimit += random.randint(0, inVariance*2) - inVariance
                inLimit = max(inLimit, 0)
            self.__log_header("{limit} {target} weights changed ({range:0.1f})".format(target=target, limit=inLimit, range=inRange))
            pmap = pmap[:inLimit]

        for p in pmap:
            weight = self.p_prompts[p]['weight'] if 'weight' in self.p_prompts[p] else 1
            self.p_prompts[p]['weight'] = self.__modify_weight(weight, inRange, inMinInput=inMinInput, inMaxInput=inMaxInput, inMinOutput=inMinOutput, inMaxOutput=inMaxOutput)
            self.__log_entry(self.p_prompts[p]['token'], "Weight changed from {before:0.2f} to {after:0.2f}".format(before=weight, after=self.p_prompts[p]['weight']))

    def TweakWeights(self, inKeywords:str, inRange:float, inLoraRange:float, inMaxOutput:float=None):
        prange = inRange
        if prange is None:
            prange = 0.0
        plorarange = inLoraRange
        if plorarange is None:
            plorarange = 0.0
        self.__log_header("Weights changed for: {keywords} ({range:0.1f}/{lorarange:0.1f})".format(keywords=inKeywords, range=prange, lorarange=plorarange))
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
                self.__log_entry(self.p_prompts[x]['token'], "Weight changed from {before:0.2f} to {after:0.2f}".format(before=weight, after=self.p_prompts[x]['weight']))

    def __match(self, inKeywords:list, inString:str):
        inString = inString.lower()
        for kw in inKeywords:
            if kw in inString:
                return True
        return False
    
    # def Shift(self, inList:list, inBefore:int, inAfter:int) -> list:
    #     return self.__shift(inList, inBefore, inAfter)
    
    def __shift(self, inList:list, inBefore:int, inAfter:int) -> list:
        if inBefore==inAfter:
            return inList
        newlist = []
        if inBefore<inAfter:
            newlist = inList[:inBefore]
            newlist += inList[inBefore+1:inAfter+1]
            newlist += inList[inBefore:inBefore+1]
            newlist += inList[inAfter+1:]
        else:
            newlist = inList[:inAfter]
            newlist += inList[inBefore:inBefore+1]
            newlist += inList[inAfter:inBefore]
            newlist += inList[inBefore+1:]

        return newlist

    def __modify_weight(self, inWeight:float, inRange:float, inMinInput:float=None, inMaxInput:float=None, inMinOutput:float=None, inMaxOutput:float=None):
        if (inMinInput is not None and inWeight<inMinInput) or (inMaxInput is not None and inWeight>inMaxInput) or inRange is None:
            return inWeight

        random.seed(self.seed)
        mod = (random.random() * inRange * 2)-inRange
        if inMinOutput is not None and (inWeight+mod) < inMinOutput:
            return inWeight
        if inMaxOutput is not None and (inWeight+mod) > inMaxOutput:
            return inWeight
        return inWeight+mod
    
    def __log_header(self, inHeader):
            self.p_log.append("= {header}".format(header=inHeader))

    def __log_entry(self, inPrompt, inEntry):
        self.p_log.append("{prompt}: {entry}".format(prompt=inPrompt, entry=inEntry))

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

        removed = []

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
            else:
                removed.append(self.p_prompts[x]['token'])

        if len(removed)>0:
            self.__log_header("{target} prompts removed".format(target=len(removed)))
            for p in removed:
                self.__log_entry(p, "Removed")

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
