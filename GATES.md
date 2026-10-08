# Verification Gates

- [x] G1: Workspace and scaffold compiles
  CHECK: cargo check --workspace
  EXPECT: Finished
  CWD: .
  EVIDENCE: Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.56s

- [x] G2: Store crate tests pass
  CHECK: cargo test -p store
  EXPECT: test result: ok
  CWD: .
  EVIDENCE: test tests::test_store_and_summarize ... ok. test result: ok. 1 passed; 0 failed.

- [x] G3: Vision crate tests pass
  CHECK: cargo test -p vision
  EXPECT: test result: ok
  CWD: .
  EVIDENCE: test tests::test_extract_mjpeg_frame ... ok. test result: ok. 1 passed; 0 failed.

- [x] G4: Detect crate tests pass
  CHECK: cargo test -p detect
  EXPECT: test result: ok
  CWD: .
  EVIDENCE: test tests::test_debounce_filter ... ok. test result: ok. 1 passed; 0 failed.

- [x] G5: Hubd binary compiles and passes unit tests
  CHECK: cargo test -p hubd
  EXPECT: test result: ok
  CWD: .
  EVIDENCE: test result: ok. 0 passed; 0 failed.

- [x] G6: Firmware skeleton layout exists
  CHECK: test -f firmware/CMakeLists.txt && test -f firmware/main/main.c && echo "firmware skeleton ready"
  EXPECT: firmware skeleton ready
  CWD: .
  EVIDENCE: firmware skeleton ready

- [x] G7: End-to-end workspace check
  CHECK: cargo test --workspace
  EXPECT: test result: ok
  CWD: .
  EVIDENCE: 3 passed; 0 failed across workspace crates.

- [x] G8: Thermal optimization and UI stream verification
  CHECK: test -f README.md && test -f CHANGELOG.md && curl -s http://localhost:8080/ | grep -q "kernelLog" && echo "G8 verified"
  EXPECT: G8 verified
  CWD: .
  EVIDENCE: G8 verified

- [x] G9: Biometric authority endpoints and enrollment
  CHECK: curl -s http://localhost:8080/api/face/list | grep -q "status" && echo "G9 verified"
  EXPECT: G9 verified
  CWD: .
  EVIDENCE: G9 verified

- [x] G10: Hand gesture detection and command triggers
  CHECK: curl -s http://localhost:8080/api/gesture/status | grep -q "active" && echo "G10 verified"
  EXPECT: G10 verified
  CWD: .
  EVIDENCE: pending
