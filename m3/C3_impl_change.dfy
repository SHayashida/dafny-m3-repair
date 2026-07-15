// ===== C3: 実装変更 (公開契約は不変、Trend の本体をガード) =====
// 契約項目: implementation behavior changed / public contracts preserved
method Percent(part: int, whole: int) returns (r: int)
  requires whole > 0               // 不変
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }

method Ratio(x: int) returns (r: int)
  ensures r == x * 100 / 4
{ r := Percent(x, 4); }

method Trend(delta: int, span: int) returns (r: int)
  requires span != 0               // 公開契約は不変
{
  if span > 0 { r := Percent(delta, span); }   // ★ C3: 本体をガード
  else        { r := 0; }                       // 挙動変化: span<0 で 0 を返す
}
