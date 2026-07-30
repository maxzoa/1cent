import test from "node:test";
import assert from "node:assert/strict";
import {ASSET, NETWORK, SELLER, options, validatePayment} from "./cli.mjs";

test("parser does not enable payment implicitly", () => {
  assert.deepEqual(options(["doctor"]), {command: "doctor"});
  assert.throws(() => validatePayment({}, "1000"), /payment disabled/);
});

test("one-call payment requires exact network asset seller and cap", () => {
  const opts = options(["call", "--pay", "--confirm-network", NETWORK,
    "--confirm-asset", ASSET, "--confirm-seller", SELLER,
    "--confirm-charge", "PAY-ONCE", "--max-atomic", "1000"]);
  assert.equal(validatePayment(opts, "1000"), 1000n);
  assert.throws(() => validatePayment(opts, "1001"), /exceeds/);
});
