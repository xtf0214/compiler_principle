
# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : WangRay
# @Software: PyCharm
def getOriginData():
    tranformFunctionData = {}
    Vn = []
    Vt = []
    with open("input.txt", 'r+', encoding="utf-8") as f:
        temp = f.readlines()
    for ind,i  in enumerate(temp):
        t = i[:-1].split(" ") #去掉换行 E -> TA
        if ind == 0: # 默认第一个Vn是开始符
            S =  i[0]
        x = tranformFunctionData.get(t[0],None)
        if x :
            x.append(t[2])
            tranformFunctionData.update( { t[0] : x } )
        else:
            tranformFunctionData[ t[0] ] = [ t[2] ]  #加入 {E : [TA,]}
        if( 'A'<=t[0] <='Z'):
            Vn.append(t[0])
        else:
            Vt.append(t[0])
        for tx in t[2]:
            if( 'A'<= tx <='Z'):
                Vn.append(tx)
            else:
                Vt.append(tx)
    Vn = getOnly(Vn)
    Vt = getOnly(Vt)
    return (Vn,Vt,tranformFunctionData,S)
def getOnly(l):
    n = []
    for x in l:
        if x not in n :
            n.append(x)
    return n
class MyChart():
    def __init__(self, mystr):
        self.mstr = mystr  # 输入的句子
        self.Vn = []  # 非终结符
        self.Vt = []  # 终结符
        tranformFunctionData = {}
        self.S = None  # 开始符
        self.first = {}  # first集合，是一个map对象，元素是"V":{ }
        self.follow = {}  # follow集合，也是一个map对象
        self.select = {}  # select集合，也是一个map对象,每个对象key是Vn;Value是一个map={"产生式","Vt集合"},{ F : { "->i" : "i" , "->(E)":"(" }  }
        self.analysisTable = []
        self.initFirstAndFollow()
        self.getFollow(self.S)
        self.getselect()
        self.row = []
        self.column = []
        self.initAnalysisTableData()
        print("预测分析表：")
        for i in self.analysisTable:
            print(i)
        print()

    def doAnaysis(self):
        myStack = ["#", self.S]
        X = myStack[-1]
        ind = 0
        a = self.mstr[ind]
        ind += 1
        while myStack:
            if X in self.Vt:
                if X == a:
                    a = self.mstr[ind]
                    ind += 1
                    myStack.pop()
                    X = myStack[-1]
                else:
                    return "error,经判断" + self.mstr + "不是符合该文法的句子"
            else:
                if X == "#":
                    if X == a:
                        return "success，经判断" + self.mstr + "是符合该文法的句子"
                    else:
                        return "error,经判断" + self.mstr + "不是符合该文法的句子"
                else:
                    prod = self.getProd(X, a)
                    if prod == "#":  # 没有对应产生式
                        return "error,经判断" + self.mstr + "不是符合该文法的句子"
                    else:  # 存在对应产生式
                        myStack.pop()
                        temp = prod[:1:-1]
                        if temp != "@":
                            myStack.extend(temp)  #
                        X = myStack[-1]

    def getselect(self):
        for k in self.tranformFunctionData.keys():  # k是Vn，E A T B F
            for prod in self.tranformFunctionData.get(k):  # prod 是Vn k=F 对应的产生式["i","(E)"]
                # 对于一个k->prod,检查prod的组成元素Vn集合，能不能同时都变成@，
                if self.checkIfTranfToKong(prod) == 1:  # 等于1表示全都能变成@
                    # 若能：tempS = prod[0]的first集合除去空∪follow(k)
                    temps = self.first.get(prod[0]).replace("@", "") + self.follow.get(k)
                else:
                    # 否则：tempS = prod[0]的first集合
                    temps = self.first.get(prod[0])
                prodToTemps = self.select.get(k, None)
                if prodToTemps is None:
                    self.select.update({k: {"->" + prod: temps}})
                else:
                    self.select.get(k).update({"->" + prod: temps})

    def checkIfTranfToKong(self, prod):
        for i in prod:  # 遍历 (E) 的每一个Vn/Vt,但凡有一个是Vt(不是空)或者有一个Vn的first不包含@，那么返回-1
            if i == "@":
                continue
            if i in self.Vt:
                return -1
            elif "@" not in self.first.get(i):
                return -1
        return 1

    def initAnalysisTableData(self):
        self.row = self.Vn.copy()
        self.column = self.Vt.copy()
        self.column.remove("@")
        self.column.append("#")
        for tempVn in self.row:  # 拿到行标
            T = self.getRowColumnPrdo(tempVn)
            self.analysisTable.append(T)

    def getRowColumnPrdo(self, tempVn):
        T = []
        for tempVt in self.column:
            mp = self.select.get(tempVn)  # {'->+TA': '+', '->@': '#)'}
            flag = 0
            for tk in mp.keys():
                if tempVt in mp.get(tk):
                    T.append(tk)
                    flag = 1
            if flag == 0:
                T.append("#")
        return T

    def getProd(self, X, a):
        x = self.row.index(X)
        y = self.column.index(a)
        return self.analysisTable[x][y]

    def initFirstAndFollow(self):
        (self.Vn, self.Vt, self.tranformFunctionData, self.S) = getOriginData()
        for t in self.Vn + self.Vt:
            if t in self.Vt:
                self.first.update({t: t})
            else:
                self.first.update({t: None})
                self.follow.update({t: ""})
        for t in self.Vn + self.Vt:
            self.getFisrt(t)
        for t in self.Vn:
            self.follow.update({t: self.getFollow(t)})

    def getFollow(self, T):
        x = self.follow.get(T)
        if x != "": return x
        if T == self.S:
            tempFollow = "#"
        else:
            tempFollow = ""
        for prodFromLeft in self.tranformFunctionData.keys():  # 遍历所有的左部 "A","P"  。 tranformFunctionData为  { "A":["+E" , "@"]  ,"P": [ "(E)","a","b","^" ]  }
            for prodFromRight in self.tranformFunctionData.get(
                    prodFromLeft):  # 遍历每个左部能够产生的右部"aTCA","TE","ABT","a","@"   ===>>> ["+E" , "@"]  [ "(E)","a","b","^" ]
                ind = prodFromRight.find(T)
                mylen = len(prodFromRight)
                if ind != -1 and mylen >= 2:  # 产生式右部满足T -> ABC的形式
                    if (ind == mylen - 1):
                        tempFollow = self.restart(tempFollow, prodFromLeft, T)
                    else:
                        tempFollow += self.first.get(prodFromRight[ind + 1]).replace("@", "")  # 除去 @ 符号

                        if (ind == mylen - 2 and prodFromRight[mylen - 1] in self.Vn and "@" in
                                self.tranformFunctionData[prodFromRight[mylen - 1]]):
                            tempFollow = self.restart(tempFollow, prodFromLeft, T)  # 进行反复传送
        return "".join(sorted(list(set(tempFollow))))

    # 求follow的反复传送函数
    def restart(self, tempFollow, prodFromLeft, T):
        if T == prodFromLeft: return tempFollow  # 有些产生式可能是 T -> aT ,这个时候不要再follow(T) = follow(T)了，会死循环
        if self.follow.get(prodFromLeft) == "" and prodFromLeft == self.S:
            tempFollow += "#"
        else:
            tempFollow += self.getFollow(prodFromLeft)
        return tempFollow

    # 求first集合
    def getFisrt(self, T):
        '''
        # 注意如果 T -> AB , A如果能产生@，那么firstB也属于First（T）
        :param T: 终结符或者非终结符
        :return String :  T的first集，
        '''
        x = self.first.get(T, None)
        if x:
            return x
        else:  # 为空，求了First,更新了self.first，再返回其first集
            tempFirst = ""
            for prodForm in self.tranformFunctionData[T]:  # 遍历所有它的产生式右部 T -> ["F" , "Ta" , "(E)" , "a" , @ ]
                tempFirst += self.getFisrt(prodForm[0])
                if len(prodForm) >= 2 and prodForm[1] in self.Vn and prodForm[0] in self.Vn and '@' in \
                        self.tranformFunctionData[prodForm[0]]:
                    tempFirst += self.getFisrt(prodForm[1])
            self.first.update({T: tempFirst})
            return tempFirst


if __name__ == "__main__":
    mstr = "i+i*i#"
    print("待判断的句子为：", mstr)
    mc = MyChart(mstr)
    print(mc.doAnaysis())


