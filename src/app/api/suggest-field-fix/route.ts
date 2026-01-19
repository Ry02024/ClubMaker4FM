import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

export async function POST(request: Request) {
    let tempFile: string | null = null;
    try {
        const { currentFields, context } = await request.json();

        if (!currentFields || !Array.isArray(currentFields)) {
            return NextResponse.json({ success: false, error: 'No current fields provided' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'suggest_field_fix.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // 一時ファイルにJSONデータを保存（コマンドライン引数の長さ制限回避）
        const tempDir = os.tmpdir();
        tempFile = path.join(tempDir, `clubmaker_suggest_${Date.now()}.json`);
        const inputData = JSON.stringify({ currentFields, context: context || '' }, null, 2);
        fs.writeFileSync(tempFile, inputData, 'utf-8');

        // ファイルパスを引数として渡す
        const command = `${pythonCommand} "${scriptPath}" --file "${tempFile}"`;

        return new Promise((resolve) => {
            exec(command, { timeout: 120000, maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
                // 一時ファイルを削除
                if (tempFile && fs.existsSync(tempFile)) {
                    try { fs.unlinkSync(tempFile); } catch (e) { /* ignore */ }
                }

                console.log('Suggest Field Fix Output:', stdout || '(empty)');
                console.log('Suggest Field Fix Output Length:', stdout?.length || 0);
                if (stderr) {
                    console.error('Suggest Field Fix Stderr:', stderr);
                    console.error('Suggest Field Fix Stderr Length:', stderr.length);
                }

                if (error) {
                    // タイムアウトエラーの場合
                    if (error.signal === 'SIGTERM' || error.message.includes('timeout')) {
                        resolve(NextResponse.json({
                            success: false,
                            error: 'Script execution timeout (120s). The request may be too large or the API is slow.',
                            details: `Command: ${command}\nStdout: ${stdout || '(empty)'}\nStderr: ${stderr || '(empty)'}`,
                            stdout: stdout || '',
                            stderr: stderr || ''
                        }, { status: 500 }));
                        return;
                    }

                    // stdoutにエラーメッセージが含まれている可能性がある
                    let errorMessage = error.message;
                    let errorDetails = stdout || stderr || '';
                    
                    // stdoutからJSONエラーを抽出
                    if (stdout && stdout.trim()) {
                        try {
                            const lines = stdout.trim().split('\n');
                            const lastLine = lines[lines.length - 1];
                            if (lastLine.trim().startsWith('{')) {
                                const parsedError = JSON.parse(lastLine);
                                if (parsedError.error) {
                                    errorMessage = parsedError.error;
                                    errorDetails = parsedError.traceback || parsedError.details || errorDetails;
                                }
                            }
                        } catch (e) {
                            // JSONパースに失敗した場合は、そのまま使用
                        }
                    }
                    
                    resolve(NextResponse.json({
                        success: false,
                        error: errorMessage,
                        details: errorDetails,
                        stdout: stdout || '',
                        stderr: stderr || '',
                        command: command
                    }, { status: 500 }));
                } else {
                    // エラーがない場合でも、stdoutが空の場合はエラーとして扱う
                    if (!stdout || !stdout.trim()) {
                        resolve(NextResponse.json({
                            success: false,
                            error: 'Script returned no output',
                            details: `Stdout: ${stdout || '(empty)'}\nStderr: ${stderr || '(empty)'}`,
                            stdout: stdout || '',
                            stderr: stderr || ''
                        }, { status: 500 }));
                        return;
                    }

                    try {
                        const lines = stdout.trim().split('\n');
                        const lastLine = lines[lines.length - 1];
                        const result = JSON.parse(lastLine);
                        resolve(NextResponse.json(result));
                    } catch (e) {
                        resolve(NextResponse.json({
                            success: false,
                            error: 'Failed to parse AI response',
                            parseError: e instanceof Error ? e.message : String(e),
                            raw: stdout,
                            stderr: stderr
                        }, { status: 500 }));
                    }
                }
            });
        });
    } catch (err: any) {
        // 一時ファイルを削除
        if (tempFile && fs.existsSync(tempFile)) {
            try { fs.unlinkSync(tempFile); } catch (e) { /* ignore */ }
        }
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
