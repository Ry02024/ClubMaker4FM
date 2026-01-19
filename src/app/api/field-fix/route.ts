import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

export async function POST(request: Request) {
    let tempFile: string | null = null;
    try {
        const { fixes } = await request.json();

        if (!fixes || !Array.isArray(fixes) || fixes.length === 0) {
            return NextResponse.json({ success: false, error: 'No fixes provided' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'field_fixer.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // 一時ファイルにJSONデータを保存（コマンドライン引数の長さ制限回避）
        const tempDir = os.tmpdir();
        tempFile = path.join(tempDir, `clubmaker_fixes_${Date.now()}.json`);
        const fixesData = JSON.stringify(fixes, null, 2);
        fs.writeFileSync(tempFile, fixesData, 'utf-8');

        // ファイルパスを引数として渡す
        const command = `${pythonCommand} "${scriptPath}" --file "${tempFile}"`;

        return new Promise((resolve) => {
            exec(command, { timeout: 300000, maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
                // 一時ファイルを削除
                if (tempFile && fs.existsSync(tempFile)) {
                    try { fs.unlinkSync(tempFile); } catch (e) { /* ignore */ }
                }

                console.log('Field Fixer Output:', stdout);
                if (stderr) console.error('Field Fixer Stderr:', stderr);

                if (error) {
                    resolve(NextResponse.json({
                        success: false,
                        error: error.message,
                        log: stdout,
                        stderr: stderr
                    }, { status: 500 }));
                } else {
                    try {
                        // 最後の行がJSONのはず
                        const lines = stdout.trim().split('\n');
                        const lastLine = lines[lines.length - 1];
                        const result = JSON.parse(lastLine);
                        resolve(NextResponse.json(result));
                    } catch (e) {
                        resolve(NextResponse.json({
                            success: true,
                            log: stdout,
                            stderr: stderr
                        }));
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
