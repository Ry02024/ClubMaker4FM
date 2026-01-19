import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

export async function POST(request: Request) {
    try {
        const { prompt } = await request.json();

        if (!prompt) {
            return NextResponse.json({ success: false, error: 'Prompt is required' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'generate_design_ai.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // プロンプトを一時ファイルに保存（改行を保持）
        const tempDir = os.tmpdir();
        const tempFile = path.join(tempDir, `clubmaker_prompt_${Date.now()}.txt`);
        fs.writeFileSync(tempFile, prompt, 'utf-8');

        // ファイルパスを引数として渡す
        const command = `${pythonCommand} "${scriptPath}" --file "${tempFile}"`;

        return new Promise((resolve) => {
            exec(command, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
                // 一時ファイルを削除
                try { fs.unlinkSync(tempFile); } catch (e) { /* ignore */ }

                // Pythonからのログ出力を表示
                if (stderr) {
                    console.log('Python Output:', stderr);
                }

                if (error) {
                    console.error('AI Generation Error:', error);
                    resolve(NextResponse.json({ success: false, error: error.message, details: stdout }, { status: 500 }));
                    return;
                }
                try {
                    const design = JSON.parse(stdout.trim());
                    resolve(NextResponse.json({ success: true, design }));
                } catch (parseError) {
                    console.error('JSON Parse Error:', parseError, stdout);
                    resolve(NextResponse.json({ success: false, error: 'Failed to parse AI response', details: stdout }, { status: 500 }));
                }
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
