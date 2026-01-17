import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    const { templateName, actionAfterClick } = await request.json();

    const scriptPath = path.join(process.cwd(), 'scripts', 'automate_action.py');
    const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

    if (!fs.existsSync(scriptPath)) {
        return NextResponse.json({ success: false, error: 'Automation script not found' }, { status: 404 });
    }

    // 引数としてテンプレート画像名を渡す
    const command = `${pythonCommand} "${scriptPath}" "${templateName}"`;

    return new Promise((resolve) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error('Automation Error:', error);
                resolve(NextResponse.json({
                    success: false,
                    error: error.message,
                    details: stdout
                }, { status: 500 }));
                return;
            }

            // クリック成功後、追加のアクション（Ctrl+Vなど）が必要な場合は、
            // ここでさらにPythonを実行するか、automate_action.py内で完結させる

            resolve(NextResponse.json({
                success: true,
                message: 'Automation executed',
                output: stdout
            }));
        });
    });
}
