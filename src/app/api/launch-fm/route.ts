import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST() {
    // Pythonスクリプトのパス
    const scriptPath = path.join(process.cwd(), 'scripts', 'launch_fm.py');
    const defaultFmPath = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\FileMaker Pro.lnk';

    if (!fs.existsSync(scriptPath)) {
        return NextResponse.json({
            success: false,
            error: 'Python起動スクリプトが見つかりません。'
        }, { status: 404 });
    }

    // Pythonスクリプトを実行
    // 仮想環境のpython.exeを優先的に使用
    const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const pythonBin = fs.existsSync(venvPythonPath) ? venvPythonPath : 'python';

    // 引数を安全にパースするため、パスを個別にクォート
    const command = `"${pythonBin}" "${scriptPath}" "${defaultFmPath}"`;

    return new Promise((resolve) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error('Launch Error:', error);
                console.error('Stdout:', stdout);
                console.error('Stderr:', stderr);
                resolve(NextResponse.json({
                    success: false,
                    error: error.message,
                    details: stderr || stdout
                }, { status: 500 }));
                return;
            }

            console.log('Python Output:', stdout);
            resolve(NextResponse.json({
                success: true,
                message: 'FileMaker launched via Python',
                output: stdout
            }));
        });
    });
}
