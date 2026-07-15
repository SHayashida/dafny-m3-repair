// ===== 元仕様 (spec version v0): verification が失敗する =====
// callee: 本体は whole != 0 なら定義される（Dafnyの整数除算は非ゼロ除数で全域）。
//         しかし契約は whole > 0 に限定 = 過剰に狭い仕様。
method Percent(part: int, whole: int) returns (r: int)
  requires whole > 0
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }

// 既存の検証済みクライアント（正の whole を渡す）。C2互換性テスト用。
method Ratio(x: int) returns (r: int)
  ensures r == x * 100 / 4
{ r := Percent(x, 4); }

// 壊れたクライアント: 呼び手が保証するのは「非ゼロ」のみ（負もあり得る）。
method Trend(delta: int, span: int) returns (r: int)
  requires span != 0
{ r := Percent(delta, span); }   // FAIL: whole > 0 を確立できない
