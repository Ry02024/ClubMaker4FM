'use client';

import { useState, useEffect } from 'react';
import { generateFieldsXML, generateTableXML, generateLayoutXML, FMTable } from '@/lib/fm-xml';

const PRESET_PROMPT = `夜店クラブの「伝票・売上管理」ミニマムシステム
- 伝票テーブル(dp): 日付, tableno, total, castid, custid, paytype
- 設定テーブル(app): var_cast (JSON), 当日売上集計
- 1画面入力→自動計算→ランキング出力`;

export default function Home() {
  const [prompt, setPrompt] = useState(PRESET_PROMPT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [viewMode, setViewMode] = useState<'schema' | 'layout'>('schema');
  const [design, setDesign] = useState<{
    tables: FMTable[],
    layouts?: any[],
    thoughts?: string[]
  } | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [status, setStatus] = useState<{ msg: string; isError: boolean } | null>(null);
  const [cooldown, setCooldown] = useState(0);

  // クールダウンのカウントダウン
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(prev => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  // スクリーンショット一覧を取得
  const fetchScreenshots = async () => {
    try {
      const res = await fetch('/api/screenshots');
      const data = await res.json();
      setScreenshots(data.screenshots || []);
    } catch (err) {
      console.error('Failed to fetch screenshots');
    }
  };

  useEffect(() => {
    fetchScreenshots();
  }, []);

  const handleLaunchFM = async () => {
    setIsLaunching(true);
    setStatus({ msg: 'FileMakerを起動中...', isError: false });
    try {
      const res = await fetch('/api/launch-fm', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ FileMakerを起動しました', isError: false });
    } catch (err: any) {
      setStatus({ msg: `❌ 起動失敗: ${err.message}`, isError: true });
    } finally {
      setIsLaunching(false);
    }
  };

  const handleCapture = async () => {
    setIsCapturing(true);
    setStatus({ msg: '画面をキャプチャ中...', isError: false });
    try {
      // 実際には専用のAPIが必要ですが、ここではlaunch-fmと同様にPythonを叩くAPIを想定
      // (後ほど /api/capture-screen を作成)
      const res = await fetch('/api/capture-screen', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ キャプチャ完了', isError: false });
      await fetchScreenshots();
    } catch (err: any) {
      setStatus({ msg: `❌ キャプチャ失敗: ${err.message}`, isError: true });
    } finally {
      setIsCapturing(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt) {
      setStatus({ msg: '指示を入力してください', isError: true });
      return;
    }
    setIsGenerating(true);
    setStatus({ msg: 'AIがFileMakerの設計図を作成中...', isError: false });

    try {
      const res = await fetch('/api/generate-design', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || '生成に失敗しました');
      }

      // AIの返答が階層化されている場合（{ tables: [...] } ではなく { design: { tables: [...] } } など）に対応
      let extractedDesign = data.design;
      if (!extractedDesign.tables && extractedDesign.design?.tables) {
        extractedDesign = extractedDesign.design;
      }

      // 単数形 (table) で返してくるケースへの対応
      if (!extractedDesign.tables && extractedDesign.table) {
        extractedDesign.tables = Array.isArray(extractedDesign.table) ? extractedDesign.table : [extractedDesign.table];
      }

      if (!extractedDesign.tables && extractedDesign.layouts) {
        // layoutsはあるがtablesがない、という特殊ケースへの防御
        extractedDesign.tables = [];
      }

      if (!extractedDesign.tables || !Array.isArray(extractedDesign.tables)) {
        console.error('Invalid design structure:', extractedDesign);
        const details = extractedDesign.details ? `\n詳細:\n${extractedDesign.details.join('\n')}` : '';
        throw new Error(`AIの返答形式が正しくありません (tablesが見つかりません)。内容: ${JSON.stringify(extractedDesign).substring(0, 100)}...${details}`);
      }

      setDesign({
        tables: extractedDesign.tables,
        layouts: extractedDesign.layouts || [],
        thoughts: extractedDesign.thoughts || []
      });
      // レイアウトがあれば自動的にレイアウト表示へ
      if (extractedDesign.layouts?.length > 0) {
        setViewMode('layout');
      }
      setStatus({ msg: '✅ 設計図が完成しました！内容を確認してください', isError: false });
    } catch (err: any) {
      console.error(err);
      setStatus({ msg: `❌ エラー: ${err.message}`, isError: true });
    } finally {
      setIsGenerating(false);
      setCooldown(10); // 10秒のクールダウン
    }
  };

  const copyToFM = async (xml: string) => {
    setStatus({ msg: 'クリップボードに登録中...', isError: false });
    try {
      const res = await fetch('/api/copy-fm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xml }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ クリップボードに登録完了！FileMakerで貼り付けできます。', isError: false });
    } catch (err: any) {
      setStatus({ msg: `❌ エラー: ${err.message}`, isError: true });
    }
  };

  const handleCreateFieldGUI = async (name: string, type: string, comment: string = 'AI生成') => {
    setStatus({ msg: `GUI操作でフィールド "${name}" を生成中...`, isError: false });
    try {
      const res = await fetch('/api/create-field-gui', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, comment }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: `✅ フィールド "${name}" の生成命令を送信しました（FileMakerを確認してください）`, isError: false });
    } catch (err: any) {
      console.error(err);
      setStatus({ msg: `❌ GUI生成エラー: ${err.message}`, isError: true });
    }
  };

  const handleFinalizeFM = async () => {
    setStatus({ msg: '変更を保存してダイアログを閉じています...', isError: false });
    try {
      const res = await fetch('/api/finalize-fm-dialog', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
    } catch (err: any) {
      console.error('Finalize failed:', err);
    }
  };

  const handleBatchCreateGUI = async (fields: any[]) => {
    if (!confirm(`${fields.length} 個のフィールドを順番にGUI生成します。既に存在するフィールドはスキップされます。よろしいですか？`)) return;

    setStatus({ msg: 'FileMakerの現在の状態を確認中...', isError: false });
    let existingFields: string[] = [];
    try {
      const res = await fetch('/api/get-fm-fields');
      const data = await res.json();
      if (data.success) {
        existingFields = data.fields.map((f: string) => f.toLowerCase());
      }
    } catch (err) {
      console.warn('進捗の取得に失敗しました。全件作成を試みます。', err);
    }

    // 未作成のフィールドのみを抽出
    const remainingFields = fields.filter(f => !existingFields.includes(f.name.toLowerCase()));

    if (remainingFields.length === 0) {
      setStatus({ msg: '✅ 全てのフィールドは既に存在します。', isError: false });
      await handleFinalizeFM();
      return;
    }

    setStatus({ msg: `${remainingFields.length} 個の未生成フィールドを処理します...`, isError: false });

    for (const f of remainingFields) {
      await handleCreateFieldGUI(f.name, f.type, 'ClubMakerによる自動生成');
      // 次の操作まで少し待機
      await new Promise(r => setTimeout(r, 1500));
    }
    await handleFinalizeFM();
    setStatus({ msg: '✅ 全てのGUI生成プロセスが完了し、保存されました。', isError: false });
  };

  return (
    <main className="min-h-screen bg-[#0a0a0c] text-slate-100 p-6 font-sans selection:bg-purple-500/30">
      {/* 背景装飾 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-pink-900/10 blur-[120px] rounded-full"></div>
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <header className="flex justify-between items-center bg-white/5 backdrop-blur-md border border-white/10 p-4 rounded-2xl shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-tr from-purple-600 to-pink-600 rounded-xl flex items-center justify-center font-bold text-xl shadow-lg shadow-purple-500/20">
              C
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                CLUB MAKER
              </h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
                AI Powered FileMaker Automator
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleLaunchFM}
              disabled={isLaunching}
              className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 text-sm font-semibold active:scale-95 disabled:opacity-50"
            >
              <span className={isLaunching ? 'animate-spin' : ''}>🚀</span>
              {isLaunching ? '起動中...' : 'FileMaker 起動'}
            </button>
            <button
              onClick={handleCapture}
              disabled={isCapturing}
              className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-purple-500/20 transition-all active:scale-95 disabled:opacity-50"
            >
              📸 画面をキャプチャ
            </button>
          </div>
        </header>

        {/* Status Bar */}
        {status && (
          <div className={`p-4 rounded-xl border animate-in slide-in-from-top-2 duration-300 ${status.isError ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-green-500/10 border-green-500/30 text-green-400'
            }`}>
            <div className="flex items-center gap-3 text-sm font-medium">
              <span className={`w-2 h-2 rounded-full ${status.isError ? 'bg-red-500' : 'bg-green-500'} animate-pulse`}></span>
              {status.msg}
            </div>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-180px)]">
          {/* Left: Input Design */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-hidden">
            <section className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col shadow-xl">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="w-1.5 h-6 bg-purple-500 rounded-full"></span>
                AIへの指示
              </h2>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="flex-1 w-full bg-black/40 border border-white/5 rounded-2xl p-4 text-slate-300 text-sm focus:ring-2 focus:ring-purple-500 outline-none transition-all resize-none font-mono"
                placeholder="どのようなシステムを作りますか？"
              />
              <button
                onClick={handleGenerate}
                disabled={isGenerating || cooldown > 0}
                className="w-full mt-4 py-4 bg-white text-black font-black rounded-2xl transition-all hover:bg-slate-200 active:scale-95 shadow-xl shadow-white/5 disabled:opacity-50"
              >
                {isGenerating ? '生成中...' : cooldown > 0 ? `待機中 (${cooldown}s)` : 'システムを生成する'}
              </button>

              {isGenerating && (
                <div className="mt-6 p-4 bg-white/5 border border-white/5 rounded-2xl animate-pulse">
                  <p className="text-[10px] text-slate-500 font-bold uppercase mb-2">AIが考えたこと：</p>
                  <p className="text-xs text-slate-400 italic">利用者様の意図を汲み取り、最適なテーブル構造を構築しています...</p>
                </div>
              )}

              {design?.thoughts && (
                <div className="mt-6 p-4 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
                  <p className="text-[10px] text-purple-400 font-bold uppercase mb-2 tracking-widest leading-loose">🎯 生成のポイント：</p>
                  <ul className="space-y-2">
                    {design.thoughts.map((thought, i) => (
                      <li key={i} className="text-xs text-slate-400 flex gap-2">
                        <span className="text-purple-500">•</span>
                        {thought}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          </div>

          {/* Center: Schema Preview */}
          <div className="col-span-12 lg:col-span-6 flex flex-col gap-6 overflow-hidden">
            {design && (
              <div className="flex gap-4 p-1 bg-black/40 border border-white/5 rounded-2xl w-fit">
                <button
                  onClick={() => setViewMode('schema')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'schema' ? 'bg-white text-black shadow-lg shadow-white/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  Schema
                </button>
                <button
                  onClick={() => setViewMode('layout')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'layout' ? 'bg-white text-black shadow-lg shadow-white/10' : 'text-slate-500 hover:text-slate-300'}`}
                >
                  Modern Layout
                </button>
              </div>
            )}

            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {!design ? (
                <div className="h-full bg-white/[0.02] border border-dashed border-white/10 rounded-3xl flex flex-col items-center justify-center p-12 text-slate-600">
                  <div className="text-8xl mb-6 opacity-20">📐</div>
                  <p className="text-xl font-bold opacity-40">設計案がここに表示されます</p>
                  <p className="text-sm opacity-30 mt-2">左のパネルから指示を入力してください</p>
                </div>
              ) : viewMode === 'schema' ? (
                <div className="space-y-6">
                  {(!design?.tables || design.tables.length === 0) ? (
                    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-12 text-center text-slate-500">
                      <p className="text-xl font-bold">テーブル構造が見つかりませんでした</p>
                      <p className="text-sm mt-2">AIの出力を解析できませんでした。もう一度指示を変えて試してみてください。</p>
                    </div>
                  ) : (
                    design.tables.map((table) => (
                      <div key={table.name} className="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                        <div className="bg-white/5 p-6 flex justify-between items-center border-b border-white/5">
                          <div>
                            <h3 className="text-2xl font-black text-purple-400">
                              {table.name}
                            </h3>
                            <p className="text-[10px] text-slate-500 uppercase font-bold mt-1 tracking-widest">Database Table</p>
                          </div>
                          <div className="flex gap-3">
                            <button
                              onClick={() => copyToFM(generateFieldsXML(table.fields))}
                              className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 border border-purple-500/30 rounded-xl text-xs font-bold transition-all active:scale-95"
                            >
                              フィールドをコピー
                            </button>
                            <button
                              onClick={() => handleBatchCreateGUI(table.fields)}
                              className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-bold transition-all active:scale-95"
                            >
                              一括GUI生成
                            </button>
                          </div>
                        </div>
                        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                          {table.fields.map((field) => (
                            <div key={field.name} className="group bg-black/40 border border-white/5 p-4 rounded-2xl hover:border-purple-500/50 transition-all duration-300">
                              <div className="flex justify-between items-start mb-2">
                                <span className="text-[10px] px-2 py-0.5 bg-white/10 text-slate-400 rounded-full font-bold uppercase">
                                  {field.type}
                                </span>
                              </div>
                              <div className="font-mono text-lg font-bold text-slate-200 group-hover:text-white transition-colors flex justify-between items-center">
                                {field.name}
                                <button
                                  onClick={() => handleCreateFieldGUI(field.name, field.type)}
                                  className="opacity-0 group-hover:opacity-100 p-1.5 bg-white/10 hover:bg-white/20 rounded-lg transition-all text-[10px]"
                                  title="単体GUI作成"
                                >
                                  🏗️
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <div className="space-y-12 pb-20">
                  {design.layouts?.map((lyt: any, idx: number) => (
                    <div key={idx} className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden group">
                      {/* Decorative Background */}
                      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 blur-[100px] pointer-events-none" />

                      <div className="relative z-10">
                        <div className="flex justify-between items-start mb-10">
                          <div>
                            <h3 className="text-3xl font-black text-white tracking-tight">
                              {lyt.name}
                            </h3>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold uppercase tracking-widest text-slate-400 border border-white/5">
                                {lyt.type}
                              </span>
                              <span className="text-slate-500 text-xs">for {lyt.table}</span>
                            </div>
                          </div>
                          <div className="flex gap-4 items-center">
                            <button
                              onClick={() => copyToFM(generateLayoutXML(lyt))}
                              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-purple-500/20 transition-all active:scale-95"
                            >
                              レイアウトXMLをコピー
                            </button>
                            <div className="flex gap-2">
                              <div className="w-8 h-8 rounded-full shadow-inner border border-white/10" style={{ backgroundColor: lyt.style?.primaryColor }}></div>
                              <div className="w-8 h-8 rounded-full shadow-inner border border-white/10" style={{ backgroundColor: lyt.style?.accentColor }}></div>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-12 gap-4 bg-white/[0.02] border border-white/5 p-6 rounded-3xl min-h-[400px]">
                          {lyt.elements?.map((el: any, i: number) => (
                            <div
                              key={i}
                              style={{
                                gridColumn: `span ${el.grid.w}`,
                                gridRow: `span ${el.grid.h}`,
                              }}
                              className="bg-white/5 border border-white/10 rounded-2xl p-4 hover:border-white/30 transition-all group/el flex flex-col justify-center"
                            >
                              <label className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-tighter">
                                {el.label}
                              </label>
                              <div className="h-10 bg-black/20 rounded-lg border border-white/5 flex items-center px-4 text-xs text-slate-400 italic">
                                {el.field}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                  {(!design.layouts || design.layouts.length === 0) && (
                    <div className="h-64 flex flex-col items-center justify-center text-slate-500 opacity-60">
                      <div className="text-6xl mb-4">✨</div>
                      <p className="text-xl font-bold italic text-center">
                        レイアウト案が生成されませんでした<br />
                        <span className="text-sm font-normal not-italic mt-2 block">指示を詳しくして再生成をお試しください</span>
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          {/* Right: Assets & History */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-hidden text-sm">
            <section className="flex-1 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col shadow-xl overflow-hidden">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="w-1.5 h-6 bg-pink-500 rounded-full"></span>
                キャプチャ履歴
              </h2>
              <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                {screenshots.length === 0 ? (
                  <div className="h-40 flex flex-col items-center justify-center text-slate-500 opacity-60 italic">
                    画像がありません
                  </div>
                ) : (
                  screenshots.map((src, i) => (
                    <div key={i} className="group relative aspect-video bg-black/40 rounded-xl overflow-hidden border border-white/5 hover:border-pink-500/50 transition-all cursor-pointer shadow-lg">
                      <img src={src} alt="Capture" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                        <span className="text-[10px] font-bold text-white truncate w-full">{src.split('/').pop()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </main>
  );
}
