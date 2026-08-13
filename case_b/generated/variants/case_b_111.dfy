// Canonical Case B source.  This fully retained program is intentionally
// expected to fail verification because x is unrestricted while y must be
// nonnegative.
//
// CASE_B_METADATA {"construct_kind":"caller_obligation","deleted_semantics":"Add the public precondition x >= 0.","lever_id":"L1_REQUIRE_NONNEGATIVE","report_group":"INPUT_CONTRACT","retained_semantics":"The public method accepts every integer x.","source_location":"Nonnegative.requires"}
// CASE_B_METADATA {"construct_kind":"caller_obligation","deleted_semantics":"Add the weaker public precondition x >= -1.","lever_id":"L2_REQUIRE_AT_LEAST_MINUS_ONE","report_group":"INPUT_CONTRACT","retained_semantics":"No lower-bound precondition is added.","source_location":"Nonnegative.requires"}
// CASE_B_METADATA {"construct_kind":"implementation_body","deleted_semantics":"Assign y := x + 1.","lever_id":"L3_SHIFT_BODY_BY_ONE","report_group":"IMPLEMENTATION_BODY","retained_semantics":"Assign y := x.","source_location":"Nonnegative.body.assignment"}

method Nonnegative(x: int) returns (y: int)
  requires x >= 0
  requires x >= -1
  ensures y >= 0
{
  y := x + 1; // CASE_B_BODY_SLOT
}
