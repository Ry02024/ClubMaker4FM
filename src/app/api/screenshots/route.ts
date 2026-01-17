import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
    const screenshotDir = path.join(process.cwd(), 'public', 'screenshots');

    // publicフォルダがない場合は作成
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
        return NextResponse.json({ screenshots: [] });
    }

    try {
        const files = fs.readdirSync(screenshotDir);
        const screenshots = files
            .filter(file => file.endsWith('.png') || file.endsWith('.jpg'))
            .sort((a, b) => {
                // ファイル名（タイムスタンプ含む）で降順ソート
                return fs.statSync(path.join(screenshotDir, b)).mtime.getTime() -
                    fs.statSync(path.join(screenshotDir, a)).mtime.getTime();
            })
            .map(file => `/screenshots/${file}`);

        return NextResponse.json({ screenshots });
    } catch (err) {
        return NextResponse.json({ screenshots: [], error: 'Failed to read screenshots' }, { status: 500 });
    }
}
