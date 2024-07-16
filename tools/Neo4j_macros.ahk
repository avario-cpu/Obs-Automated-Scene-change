﻿#Persistent
#NoEnv
#SingleInstance force
SetTitleMatchMode, 2 ; Allows for partial matching of the window title

targetWindowTitle := "neo4j@bolt://localhost:7687/neo4j - Neo4j Browser"

MatchNode() {
    SendInput, MATCH(
    Input, UserInput, L2
    SendInput, %UserInput%){Shift down}{Enter}{Shift up}WHERE apoc.node.id(%UserInput%)=
}

MatchNodeGroup() {
    SendInput, MATCH(a:)-[r]-(b)
    SendInput {Shift down}{Enter}{Shift up}RETURN a,r,b
    Send, {Up}{Left 4}
    Input, Input1, L1
    SendInput, % HandleNodeInput(Input1)
}

MatchNodeOutPath() {
    SendInput, MATCH p=(a)-[r*]->(b)
    SendInput {Shift down}{Enter}{Shift up}WHERE apoc.node.id(a)=
    SendInput {Shift down}{Enter}{Shift up}RETURN p
    Send, {Up}{End}
}

MatchLabelsOnPath(arg) {
    SendInput, MATCH p%arg%=(x%arg%)-[R%arg%*]->(y%arg%)
    SendInput, {Shift down}{Enter}{Shift up}WHERE apoc.node.id(x%arg%)=
    SendInput, {Shift down}{Enter}{Shift up}WITH p%arg%, [n IN nodes(p%arg%) WHERE "" IN labels(n)] AS matchNodes%arg%
    Loop, 6
    {
        Send, ^{Left}
        Sleep, 10
    }
    Send, {Left 2}
    Input, Input2, L1
    SendInput, % HandleNodeInput(Input2)
    SendInput, {End}{Shift down}{Enter}{Shift up}UNWIND matchNodes%arg% AS x%arg%
    SendInput, {Up 2}{End}
}

MatchRelationship() {
    SendInput, MATCH(
    Input, Input1, L2
    SendInput, %Input1%)-[
    Input, Input2, L2
    SendInput, %Input2%%suffix%]->(
    Input, Input3, L2
    SendInput, %Input3%)
    SendInput, % HandleRelationshipInput(Input4)
    SendInput, {Shift down}{Enter}{Shift up}WHERE apoc.rel.id(%Input2%)=
}

MatchRelationshipGroup() {
    SendInput, MATCH(a)-[r:]-(b)
    SendInput, {Shift down}{Enter}{Shift up}RETURN a,r,b
    Send, {Up}
    Input, Input1, L1
    SendInput, % HandleRelationshipInput(Input1)
}

MatchPropertyKey() {
    SendInput, MATCH (a)-[r]->(b)
    SendInput, {Shift down}{Enter}{Shift up}WHERE any(key IN keys(r) WHERE key = "")
    SendInput, {Shift down}{Enter}{Shift up}RETURN a,r,b
    SendInput, {Up}{End}{Left 2}
}

MatchNodesOutPath(){
    SendInput, MATCH p0=(x0)-[R0*]->(y0)
    SendInput, {Shift down}{Enter}{Shift up}WHERE apoc.node.id(x0)=
}

CreateRelationship() {
    SendInput, CREATE(
    Input, Input1, L2
    SendInput, %Input1%)-[
    Input, Input2, L2
    SendInput, %Input2%:]->(
    Input, Input3, L2
    SendInput, %Input3%)
    Send, ^{Left}^{Left}{Right}
    Input, Input4, L1
    SendInput, % HandleRelationshipInput(Input4)
    Send, {End}{Shift down}{Enter}{Shift up}
}

CreateRelationshipNoLabel() {
    SendInput, CREATE(
    Input, Input1, L2
    SendInput, %Input1%)-[:]->(
    Input, Input3, L2
    SendInput, %Input3%)
    Send, ^{Left}{Left 4}
    Input, Input4, L1
    SendInput, % HandleRelationshipInput(Input4)
    Send, {End}{Shift down}{Enter}{Shift up}
}

CreateNode() {
    SendInput, CREATE(
    Input, Input1, L2
    SendInput, %Input1%:
        Input, Input2, L1
        SendInput, % HandleNodeInput(Input2)
        SendRaw, {text:""}
        Send, {Left 2}
    }

SetText() {
    SendInput, set{space}
    Input, Input1, L1
    SendInput, %Input1%.text=""
    Send, {Left}
}

HandleRelationshipInput(input) {
    if (GetKeyState("Alt", "P") && GetKeyState("Shift", "P")) {
        if (input = "d") {
            return "DELAYS"
        }
    } else if (GetKeyState("Shift", "P")) {
        if (input = "a") {
            return "ALLOWS"
        }
        if (input = "d") {
            return "DISABLES"
        }
        if (input = "l") {
            return "LISTENS"
        }
    } else {
        if (input = "a") {
            return "ATTEMPTS"
        }
        if (input = "c") {
            return "CHECKS"
        }
        if (input = "d") {
            return "DEFAULTS"
        }
        if (input = "e") {
            return "EXPECTS"
        }
        if (input = "i") {
            return "INITIATES"
        }
        if (input = "l") {
            return "LOCKS"
        }
        if (input = "p") {
            return "PRIMES"
        }
        if (input = "r") {
            return "RESETS"
        }
        if (input = "t") {
            return "TRIGGERS"
        }
        if (input = "u") {
            return "UNLOCKS"
        }
        
        return input
    }
}


HandleNodeInput(input) {
    if (GetKeyState("Shift", "P")) {
        if (input = "r")
            return "Request"
    } else {
        if (input = "a")
            return "Answer"
        if (input = "e")
            return "Exclamation"
        if (input = "p")
            return "Prompt"
        if (input = "q")
            return "Question"
        if (input = "r")
            return "Response"
        if (input = "i")
            return "Input"
        if (input = "o")
            return "Output"
        return input
    }
}

^+m:: ; Matches Hotkey: Ctrl+Shift+M (+G for groups) (+l for labels
    if WinActive(targetWindowTitle) {
        Input, NextKey, L1
        if (NextKey = "n") {
            MatchNode()
        } 
        else if (NextKey = "r") {
            MatchRelationship()
        } 
        else if (NextKey = "k"){
            MatchPropertyKey()
        } 
        else if (NextKey = "l"){
            Input, UserInput, L1
            MatchLabelsOnPath(UserInput)
        } 
        
        else if (NextKey = "p"){
            Input, NextKey2, L1
            if (NextKey2 = "l"){
                Input, UserInput, L1
                MatchLabelsOnPath(UserInput)
            }
            else if (NextKey2 = "n"){
                MatchNodesOutPath()
            } 
        } 
        
        else if (NextKey = "g") {
            Input, NextKey2, L1
            if (NextKey2 = "n") {
                MatchNodeGroup()
            } 
            else if (NextKey2 = "r") {
                MatchRelationshipGroup()
            }
        } 
        
        else if (NextKey = "o") {
            Input, NextKey2, L1
            if (NextKey2 = "n") {
                MatchNodeOutPath()
            } 
        }
    }
return

^+c:: ; Creations Hotkey: Ctrl+Shift+C
    if WinActive(targetWindowTitle) {
        Input, NextKey, L1
        if (NextKey = "n") {
            CreateNode()
        } else if (NextKey = "r") {
            if GetKeyState("Shift", "P") {
                CreateRelationshipNoLabel()
            } else {
                CreateRelationship()
            }
        }
    }
return

^+s:: ; Set Hotkey: Ctrl+Shift+S 
    if WinActive(targetWindowTitle) {
        Input, NextKey, L1
        if (NextKey = "t") {
            SetText()
        }
    }
return

^+*:: ; With * Hotkey: Ctrl+Shift+*
    if WinActive(targetWindowTitle) {
        SendInput,^{End}{Shift down}{Enter}{Shift up}WITH *{Shift down}{Enter}{Shift up}
    }
return

^+\:: ; Return all Hotkey: Ctrl+Shift+\
    if WinActive(targetWindowTitle) {
        SendInput,^{End}{Shift down}{Enter}{Shift up}WITH *{Shift down}{Enter}{Shift up}MATCH(all){Shift down}{Enter}{Shift up}RETURN all
    }
return

^+BackSpace:: ; Return Hotkey: Ctrl+Shift+Backspace
    if WinActive(targetWindowTitle) {
        SendInput,^{End}{Shift down}{Enter}{Shift up}RETURN{Space}
    }
return
