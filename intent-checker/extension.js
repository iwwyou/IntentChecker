const vscode = require('vscode');
const WebSocket = require('ws');

let codeStack = "";  // 미완성 코드를 저장할 스택
let stackStartLine = null;  // stack의 시작 라인
let stackEndLine = null;    // stack의 끝 라인

function activate(context) {
    const ws = new WebSocket('ws://localhost:8000/ws');    
    
    ws.on('open', () => {
        console.log('Connected to the server.');
    });

    ws.on('message', (data) => {
        const response = JSON.parse(data);

        // 분석 결과가 컴파일 오류인 경우 스택에 코드 저장
        if (response.error) {
            console.log('Compile error: Saving code to stack.');
            codeStack += response.invalid_code;  // 컴파일 오류난 코드 스택에 저장
            stackEndLine = response.endLine;     // 스택의 끝 라인 업데이트
        } else {
            // 성공적으로 분석된 경우 스택 비우기
            codeStack = "";
            stackStartLine = null;
            stackEndLine = null;
        }
    });

    vscode.workspace.onDidChangeTextDocument(event => {
        const changes = event.contentChanges;
        changes.forEach(change => {
            const startLine = change.range.start.line;
            const endLine = change.range.end.line;
            const fullText = event.document.getText();

            // 변경된 코드 라인만 추출
            const changedText = fullText.split('\n').slice(startLine, endLine + 1).join('\n');

            // 엔터가 입력된 경우
            if (changedText.includes('\n')) {
                // 스택에 있는 코드와 함께 보냄
                const fullCode = codeStack + changedText;
                
                // 스택이 비어있다면 새로운 라인 시작을 설정
                if (stackStartLine === null) {
                    stackStartLine = startLine;
                }
                
                // 스택의 끝 라인은 최신 endLine으로 설정
                stackEndLine = endLine;

                // 분석기로 보낼 메시지 구성
                const message = JSON.stringify({
                    code: fullCode,
                    startLine: stackStartLine,
                    endLine: stackEndLine
                });
                ws.send(message);
            }
        });
    });
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
