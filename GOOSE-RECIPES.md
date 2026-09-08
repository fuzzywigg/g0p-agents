# Goose Recipes for FUZZYWIGG-AI

## Recipe-Based Agent Orchestration

Store all recipes in `./agentic_flows/` directory. Each recipe is a YAML file that orchestrates one agent workflow or multi-agent orchestration.

---

## Recipe 1: Quantum Algorithm Design

**File**: `./agentic_flows/quantum_algorithm_design.yaml`

```yaml
name: quantum_algorithm_design_workflow
recipe:
  version: 1.0.0
  title: Design and Optimize Quantum Algorithm for Cryptographic Operation
  settings:
    goose_provider: "anthropic"
    goose_model: "claude-opus-4"
  
  instructions: |
    You are QuantumArchitectAgent designing a quantum algorithm for FUZZYWIGG.
    
    Task: Take a cryptographic requirement and design a Cirq circuit that:
    1. Solves the cryptographic problem
    2. Is optimized for mobile devices (2MB RAM max, <500ms execution)
    3. Is quantum-safe (uses NIST-standardized post-quantum validation)
    4. Provides clear gate counts and error rate estimates
    
    You will output:
    - Cirq circuit code (Python)
    - Gate count and circuit depth
    - Estimated error rate (simulator)
    - Hardware requirements
    - Recommendation (APPROVE / ESCALATE)
  
  prompt: |
    ## Quantum Algorithm Design Task
    
    STEP 1: Read the requirement
    Check ./agentic_flows/scratchpad.txt for a task marked "PENDING_QUANTUM_DESIGN"
    
    STEP 2: Design the circuit
    - Use Google Cirq for circuit construction
    - Optimize for gate count (aim for <50 gates)
    - Include error mitigation strategies
    
    STEP 3: Validate quantum-safety
    - Verify algorithm uses NIST-standardized post-quantum approach
    - Provide rationale for cryptographic choice
    
    STEP 4: Estimate constraints
    - Gate count (actual)
    - Circuit depth (actual)
    - Estimated error rate (from simulator)
    - Memory footprint (for mobile device)
    - Execution time (on Snapdragon 8 Gen 3)
    
    STEP 5: Update scratchpad
    Mark the task as:
    - [x] Algorithm designed
    - [x] Circuit optimized
    - [x] Quantum-safe validated
    - [ ] Ready for BlockchainArchitectAgent review
    
    STEP 6: Output
    Create Python file: ./quantum_circuits/[circuit_name].py
    Include:
    - Cirq circuit code
    - Comments explaining each gate
    - Error rate estimate
    - Hardware requirements
    
    STEP 7: Decision
    IF all metrics pass constraints:
      - Mark as APPROVED
      - Update scratchpad: ready for Blockchain integration
    ELSE:
      - Escalate with specific constraint violations
      - Suggest alternative approaches
  
  extensions:
    - type: builtin
      name: developer
      timeout: 300
```

---

## Recipe 2: Smart Contract Design

**File**: `./agentic_flows/blockchain_contract_design.yaml`

```yaml
name: blockchain_contract_design_workflow
recipe:
  version: 1.0.0
  title: Design and Audit Smart Contract for Quantum-Resistant Multi-Chain
  settings:
    goose_provider: "anthropic"
    goose_model: "claude-opus-4"
  
  instructions: |
    You are BlockchainArchitectAgent designing a smart contract for FUZZYWIGG.
    
    Task: Take a quantum circuit specification and design a Solidity smart contract that:
    1. Accepts quantum circuit results as input
    2. Validates post-quantum signatures
    3. Executes multi-chain logic
    4. Passes security audit (Slither)
    
    You will output:
    - Solidity contract code
    - ABI (for mobile integration)
    - Gas cost estimates
    - Security audit results (0 critical issues)
    - Recommendation (APPROVE / ESCALATE)
  
  prompt: |
    ## Smart Contract Design Task
    
    STEP 1: Read the quantum circuit specification
    Check ./agentic_flows/scratchpad.txt for "PENDING_CONTRACT_DESIGN"
    Locate the corresponding quantum circuit file (./quantum_circuits/*.py)
    
    STEP 2: Design the contract
    - Create Solidity contract (0.8.19+)
    - Implement post-quantum signature verification (Kyber/Dilithium)
    - Define multi-chain logic (if applicable)
    - Optimize for gas efficiency
    
    STEP 3: Validate quantum-resistant cryptography
    - All signatures must use NIST-standardized post-quantum algorithm
    - No classical RSA/ECDSA for new implementations
    - Provide rationale for cryptographic choices
    
    STEP 4: Estimate costs
    - Gas per operation (actual estimate)
    - Total gas budget (for transaction)
    - Cost in ETH (at current rates)
    - Optimization opportunities (if over budget)
    
    STEP 5: Security audit
    - Run Slither on contract code
    - Fix all vulnerabilities (critical = 0, high = acceptable if documented)
    - Provide audit report
    
    STEP 6: Update scratchpad
    Mark the task as:
    - [x] Contract designed
    - [x] Post-quantum crypto integrated
    - [x] Gas optimized
    - [x] Slither audit passed
    - [ ] Ready for EdgeSecurityAgent review
    
    STEP 7: Output
    Create Solidity file: ./contracts/[contract_name].sol
    Create ABI file: ./contracts/[contract_name].abi.json
    Include:
    - Solidity contract code (fully commented)
    - Deployment instructions
    - Gas estimates
    - Slither audit report
    
    STEP 8: Decision
    IF all metrics pass constraints:
      - Mark as APPROVED
      - Update scratchpad: ready for mobile implementation
    ELSE:
      - Escalate with specific constraint violations
      - Suggest alternative approaches
  
  extensions:
    - type: builtin
      name: developer
      timeout: 300
```

---

## Recipe 3: On-Device Security Implementation

**File**: `./agentic_flows/edge_security_implementation.yaml`

```yaml
name: edge_security_implementation_workflow
recipe:
  version: 1.0.0
  title: Implement Quantum-Safe Cryptography on Mobile Device
  settings:
    goose_provider: "anthropic"
    goose_model: "claude-opus-4"
  
  instructions: |
    You are EdgeSecurityAgent implementing quantum-safe cryptography on mobile.
    
    Task: Take a smart contract ABI and quantum circuit specification, and implement:
    1. On-device key management (HSM/Secure Enclave integration)
    2. Post-quantum signature validation
    3. Data isolation ("walled garden")
    4. Battery/performance optimization
    
    You will output:
    - React Native module (cross-platform)
    - iOS Swift wrapper (for Secure Enclave)
    - Android Kotlin wrapper (for HSM)
    - Security test results (0 log leaks)
    - Recommendation (APPROVE / ESCALATE)
  
  prompt: |
    ## On-Device Security Implementation Task
    
    STEP 1: Read the smart contract ABI
    Check ./agentic_flows/scratchpad.txt for "PENDING_EDGE_SECURITY"
    Locate contract ABI file (./contracts/*.abi.json)
    
    STEP 2: Implement on-device crypto
    - Use liboqs for post-quantum cryptography
    - Integrate with hardware security (Secure Enclave on iOS, KeyStore on Android)
    - Never store plaintext keys in RAM
    - Async/background execution (don't block UI thread)
    
    STEP 3: Design data isolation ("walled garden")
    - Encrypt all sensitive data at rest (AES-256-GCM)
    - Use TLS 1.3 for network transmission
    - Validate no PII/health data leaks to system logs
    - Implement data retention policy (purge after 30 days)
    
    STEP 4: Optimize for constraints
    - Measure crypto operation time (target: <500ms)
    - Measure memory footprint (target: <10MB)
    - Measure battery drain (target: <2% per transaction)
    - Test on target device (Snapdragon 8 Gen 3 or iPhone 12+)
    
    STEP 5: Security validation
    - Run Apple security guidelines check (iOS)
    - Run Google security guidelines check (Android)
    - Test for log leaks (grep entire app for PII, health data, keys)
    - Validate key rotation protocol
    
    STEP 6: Update scratchpad
    Mark the task as:
    - [x] On-device crypto implemented
    - [x] Data isolation validated
    - [x] Performance tested
    - [x] Security reviewed
    - [ ] Ready for OrchestrationAgent approval
    
    STEP 7: Output
    Create mobile implementation files:
    - ./mobile/src/quantum/QuantumValidator.js (React Native)
    - ./mobile/ios/QuantumValidator.swift (iOS wrapper)
    - ./mobile/android/QuantumValidator.kt (Android wrapper)
    Include:
    - Source code (fully commented)
    - Test results (performance, security)
    - Integration instructions
    - Key management documentation
    
    STEP 8: Decision
    IF all metrics pass constraints:
      - Mark as APPROVED
      - Update scratchpad: ready for OrchestrationAgent deployment decision
    ELSE:
      - Escalate with specific constraint violations
      - Suggest alternative approaches (use classical algo, reduce scope, etc.)
  
  extensions:
    - type: builtin
      name: developer
      timeout: 300
```

---

## Recipe 4: Multi-Agent Orchestration (Master Recipe)

**File**: `./agentic_flows/quantum_nft_mint_orchestration.yaml`

```yaml
name: quantum_nft_mint_full_orchestration
recipe:
  version: 1.0.0
  title: Full Quantum-Blockchain-Mobile Orchestration for NFT Mint Operation
  settings:
    goose_provider: "anthropic"
    goose_model: "claude-opus-4"
  
  instructions: |
    You are OrchestrationAgent coordinating a complete quantum NFT mint operation.
    
    This recipe runs ALL THREE specialist agents in sequence and makes the final go/no-go decision.
    
    Workflow:
    1. QuantumArchitectAgent: Design quantum randomness circuit
    2. BlockchainArchitectAgent: Design mint contract with quantum validation
    3. EdgeSecurityAgent: Implement on-device signing and key management
    4. OrchestrationAgent (you): Review all outputs, resolve conflicts, make final decision
  
  prompt: |
    ## Master Orchestration Task: Quantum NFT Mint
    
    STEP 1: Initialize task in scratchpad
    Create new task entry in ./agentic_flows/scratchpad.txt:
    
    ```markdown
    ## Quantum NFT Mint - [Timestamp]
    - [ ] QuantumArchitectAgent: Design randomness circuit
    - [ ] BlockchainArchitectAgent: Design mint contract
    - [ ] EdgeSecurityAgent: Implement on-device signing
    - [ ] OrchestrationAgent: Review and decide
    
    Status: IN_PROGRESS
    Created: [Timestamp]
    Deadline: [24 hours from now]
    ```
    
    STEP 2: Run QuantumArchitectAgent recipe
    Execute: ./agentic_flows/quantum_algorithm_design.yaml
    - Design a quantum circuit for cryptographic randomness
    - Optimize for mobile execution
    - Output gate count, depth, error rate
    - Update scratchpad: [x] QuantumArchitectAgent complete
    
    STEP 3: Run BlockchainArchitectAgent recipe
    Execute: ./agentic_flows/blockchain_contract_design.yaml
    - Use quantum circuit spec from Step 2
    - Design mint contract that validates quantum randomness
    - Pass Slither security audit (0 critical)
    - Update scratchpad: [x] BlockchainArchitectAgent complete
    
    STEP 4: Run EdgeSecurityAgent recipe
    Execute: ./agentic_flows/edge_security_implementation.yaml
    - Use contract ABI from Step 3
    - Implement on-device signing and key management
    - Pass all security checks
    - Update scratchpad: [x] EdgeSecurityAgent complete
    
    STEP 5: Review all three outputs
    Check for CONFLICTS:
    
    Conflict Type 1: PERFORMANCE
    - QuantumArchitectAgent says: "Circuit requires 100 gates"
    - EdgeSecurityAgent says: "Mobile device limited to 50 gates max"
    - RESOLUTION: Ask QuantumArchitectAgent to optimize further, or escalate
    
    Conflict Type 2: SECURITY
    - BlockchainArchitectAgent says: "Need RSA for backward compatibility"
    - QuantumArchitectAgent says: "Must use post-quantum crypto"
    - RESOLUTION: Use hybrid (post-quantum + RSA), implement migration path
    
    Conflict Type 3: TIMELINE
    - All agents say: "Need 2 weeks"
    - Business needs: "Deploy tomorrow"
    - RESOLUTION: Reduce scope, increase risk, escalate to human
    
    STEP 6: Make final decision
    
    IF NO CONFLICTS AND ALL METRICS PASS:
      Decision: ✅ APPROVED FOR TESTNET DEPLOYMENT
      Next steps:
      - Deploy to Sepolia testnet
      - Run 10x test transactions
      - Monitor for failures
      - Then decide on mainnet
    
    ELSE IF CONFLICTS BUT RESOLVABLE:
      Decision: ⚠️ APPROVED WITH MODIFICATIONS
      Changes required:
      - [List specific changes]
      - Ask affected agent(s) to revise
      - Re-run recipes
      - Make final decision again
    
    ELSE (CONFLICTS UNRESOLVABLE):
      Decision: 🚨 ESCALATE TO HUMAN
      Provide: [See escalation format below]
    
    STEP 7: Escalation format (if needed)
    
    🚨 ESCALATION REQUIRED
    
    Situation: Quantum circuit depth exceeds mobile device constraint
    Agent Inputs:
      - QuantumArchitectAgent: "100 gates minimum for algorithm correctness"
      - EdgeSecurityAgent: "Device max 50 gates, else app crashes"
    Conflict: Correctness vs. Feasibility
    Risk Analysis:
      - Option A (honor Quantum): App unusable on mobile
      - Option B (honor Edge): Algorithm incorrect, security broken
      - Option C (hybrid): Use classical simulation fallback (slower but works)
    Recommendation: Option C (hybrid approach)
    
    Timeline: Need decision within 2 hours
    
    STEP 8: Log decision
    Update scratchpad with final status:
    - [x] All agents reviewed
    - [x] Conflicts resolved
    - [x] Decision: [APPROVED / APPROVED_WITH_MODIFICATIONS / ESCALATED]
    
    Create new entry in ./postmortem.md:
    
    ```markdown
    ## Decision: Quantum NFT Mint Deployment
    - **Date**: [Timestamp]
    - **Decision**: [APPROVED / ESCALATED]
    - **Agents**: QuantumArchitectAgent, BlockchainArchitectAgent, EdgeSecurityAgent
    - **Conflicts**: [List any conflicts]
    - **Resolution**: [How were they resolved]
    - **Risk Level**: [LOW / MEDIUM / HIGH]
    - **Next Steps**: [What happens next]
    ```
  
  extensions:
    - type: builtin
      name: developer
      timeout: 600  # Long timeout for multi-step orchestration
```

---

## How to Use These Recipes

### Step 1: Individual Recipe (Single Agent)

```bash
# Design a quantum algorithm
goose run ./agentic_flows/quantum_algorithm_design.yaml

# Design a smart contract
goose run ./agentic_flows/blockchain_contract_design.yaml

# Implement mobile security
goose run ./agentic_flows/edge_security_implementation.yaml
```

### Step 2: Master Recipe (All Agents)

```bash
# Orchestrate the entire NFT mint workflow
goose run ./agentic_flows/quantum_nft_mint_full_orchestration.yaml
```

This will:

1. Run all three specialist agents
2. Collect their outputs
3. Check for conflicts
4. Make final go/no-go decision
5. Log everything in postmortem.md

---

## Scratchpad State Machine

Every recipe updates `./agentic_flows/scratchpad.txt` with checkbox progress:

```markdown
## Task: Design Quantum-Safe NFT Mint
- [x] QuantumArchitectAgent: Design circuit
- [x] BlockchainArchitectAgent: Design contract
- [ ] EdgeSecurityAgent: Mobile implementation
- [ ] OrchestrationAgent: Final approval

Status: IN_PROGRESS
Created: 2025-12-13T14:00:00Z
Deadline: 2025-12-14T14:00:00Z
Current Owner: EdgeSecurityAgent
```

This is the **source of truth** for agent coordination.

---

## Recipe Naming Convention

All recipes should follow this naming pattern:

```text
[domain]_[action]_[target].yaml

Examples:
- quantum_algorithm_design.yaml
- quantum_algorithm_validate.yaml
- blockchain_contract_design.yaml
- blockchain_contract_audit.yaml
- edge_security_implementation.yaml
- edge_security_test.yaml
- orchestration_nft_mint.yaml
- orchestration_conflict_resolution.yaml
```

---

## Adding New Recipes

When you need a new workflow:

1. **Create new YAML file** in `./agentic_flows/`
2. **Follow the structure** above (instructions, prompt, extensions)
3. **Add to README** with description
4. **Update AGENTS.md** if it defines new constraints
5. **Document** expected inputs/outputs
