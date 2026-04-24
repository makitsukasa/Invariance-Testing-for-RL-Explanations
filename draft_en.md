# Detecting Spurious Dependencies in Surrogate Explanations of RL Policies via Invariance Testing

## Abstract

We propose a framework that diagnoses the explanation quality of arbitrary interpretable models post hoc, without degrading performance, through a **decoupling** approach: a structurally constrained distillation model (Surrogate model) is deployed alongside a black-box policy learned via reinforcement learning (Oracle policy), which remains unmodified. The central claims of this work are threefold. First, a high action agreement (AA) of the Surrogate model is merely a **necessary condition** for it to serve as an explanation candidate. Second, invariance under distribution shift can be used as an additional evaluation axis to identify states where "AA is high but the explanation is wrong." Third, because the two-axis evaluation of fidelity and invariance is agnostic to the internal structure of the Surrogate model, arbitrary interpretable models can be compared on a common basis. Through experiments using an augmented CartPole environment and a Spurious GridWorld, we empirically demonstrate cases where a Surrogate model that replicates spurious dependencies achieves high AA on the training distribution yet collapses under distribution shift, as well as cases where AA is relatively preserved in a spurious-free environment. Note that this framework detects spurious dependencies but cannot confirm their absence.

## 1. Introduction

The trade-off between explainable models having low performance and high-performance models being difficult to interpret has long been identified as a fundamental constraint in XAI. Decision trees and linear models have readable structures but perform substantially worse in sequential decision-making tasks such as reinforcement learning, while post-hoc explanation methods like LIME[^8] and SHAP[^4] leave the original model untouched but provide no guarantee of how faithfully they capture the original policy's behavior (Chen et al., 2022[^1]). Recent work framing explanations as interactive, co-constructed processes (Mindlin et al., 2025[^2]) highlights the limitations of static explanations. A detailed discussion of the relationship to prior work is provided in Section 2.

This work circumvents the trade-off through **decoupling**. The high-performance policy learned via reinforcement learning (Oracle policy) is left entirely unmodified, and a structurally constrained distillation model (Surrogate model) is deployed alongside it. The Oracle policy is responsible for performance, while the Surrogate model serves as a structural candidate for explanation. Note that while "Surrogate model" can refer to an approximation of an objective function in optimization contexts, this paper follows XRL convention (Vasic et al., 2019[^3]; Bastani et al., 2018[^6]) and uses the term to denote an interpretable model that post-hoc imitates a learned policy. Precise definitions of each term are given in Section 3.

However, even if a Surrogate model can imitate the Oracle policy with high AA, should its explanations be trusted? Prior work on policy distillation (Bastani et al., 2018[^6]; Vasic et al., 2019[^3]) has treated maximizing AA as the goal, but lacks mechanisms to detect when a high-AA surrogate has copied the same spurious dependencies as the original policy. In RL, a policy's action selection determines the subsequent state transitions, and a single error can cause the entire subsequent action sequence to collapse. Consequently, a Surrogate model that faithfully replicates spurious dependencies will fail catastrophically under distribution shift. This work proposes a framework that diagnoses explainability from two perspectives: **fidelity** (action agreement on the training distribution) and **invariance under distribution shift** (maintenance of AA and policy performance after the shift). The contributions of this work are threefold:

1. We propose a framework that circumvents the explainability-performance trade-off through decoupling, enabling post-hoc evaluation of the explanation quality of arbitrary Surrogate models without compromising Oracle policy performance. Because the framework is agnostic to the internal structure of the Surrogate model, decision trees, MoET, linear models, and future interpretable models can all be compared on common evaluation axes.
2. We provide a two-stage evaluation methodology combining fidelity (AA) and invariance (AA and $J_S$ under distribution shift), and empirically demonstrate that the state of "high AA but incorrect" can be identified from numerical indicators (Experiment 2 provides direct evidence; Experiment 3 provides contrastive evidence).
3. Through experiments using CartPole and Spurious GridWorld, we show how fidelity and invariance vary with the strength of structural constraints, input distribution, and dependency structure, providing initial evidence that the two-axis evaluation logic applies beyond the primary experimental environments. As preliminary appendix-level validation, LunarLander-v3 and MuJoCo Hopper-v5 experiments (Appendices 4 and 5) suggest applicability to continuous dynamical systems, though full validation in continuous control remains future work.

## 2. Related Work

### 2.1 Policy Distillation and Surrogate Models

Research on approximating black-box policies with interpretable models has been advanced in the context of policy distillation. MoET by Vasic et al. (2019) distills neural network policies into a mixture-of-expert-trees model with soft gating, balancing interpretability and accuracy. Decision tree distillation by Bastani et al. (2018)[^6] and linear model approximation (Kolter & Ng, 2009[^7]) similarly aim to achieve structural simplicity while preserving policy behavior. These works treat AA maximization as evidence of success but lack mechanisms to detect when a high-AA surrogate has copied the same spurious dependencies as the original policy. This work addresses this gap through invariance evaluation.

### 2.2 Post-hoc Explanation Methods and Faithfulness

LIME (Ribeiro et al., 2016[^8]) and SHAP (Lundberg & Lee, 2017[^4]) are widely used methods for computing local feature attributions for individual predictions. These methods reveal "which features the policy currently depends on" but do not address whether those dependencies remain valid under distributional changes. Research on faithfulness (Alvarez-Melis & Jaakkola, 2018[^9]; Samek et al., 2017[^10]) attempts to evaluate the fidelity of explanations within the training distribution but does not address the maintenance of fidelity outside it. The concept of invariance in this work complements these approaches by directly evaluating whether faithfulness is maintained out of distribution. A comparative experiment applying Comprehensiveness faithfulness (DeYoung et al., 2020[^20]) to the same experiments (Appendix 6) quantitatively demonstrates this complementarity.

### 2.3 Invariance and Interpretability under Distribution Shift

IRM (Arjovsky et al., 2019[^5]) is a learning strategy that seeks to avoid dependence on spurious correlations by learning feature representations that are consistently effective across multiple environments. Concept bottleneck models (Koh et al., 2020[^11]) use human-defined concepts as intermediate representations to enhance the causal meaning of explanations. Post-hoc concept bottleneck models (Yuksekgonul et al., 2023[^13]) extend this to be applicable to any pretrained model without retraining, sharing with our work the stance of post-hoc evaluation. Whereas these approaches aim to endow models with interpretable representations, our work differs in providing a framework for post-hoc measurement of whether the dependencies of a trained policy are spurious.

It should be noted that the operation of evaluating models under distribution shift is also employed in OOD robustness research (Gulrajani & Lopez-Paz, 2021[^15]; Sagawa et al., 2020[^16]), but the objectives are fundamentally different. OOD robustness research asks about training strategies that improve post-shift performance. Our framework does not alter training strategies; instead, it uses distribution shift as a post-hoc tool for diagnosing the explanation quality of existing distilled Surrogate models. The goal is not achieving robustness but establishing an evaluation methodology that provides common evaluation axes for arbitrary interpretable models.

### 2.4 Explainability in RL

In the context of reinforcement learning, methods such as attention mechanism visualization (Greydanus et al., 2018[^12]) have been proposed. Puiutta & Veith (2020)[^17] comprehensively survey explainability research in RL, organizing the diversity of explanation targets and forms. This work does not directly compete with these methods but is positioned as an evaluation axis that addresses the cross-cutting question: "Does the generated explanation truly capture the policy's behavior?" In the context of "interactive, co-constructed explanations" highlighted by Mindlin et al. (2025[^2]), automatically evaluating whether explanation candidates remain valid under distributional changes as a preliminary step before human interaction can provide a better foundation for such dialogue. Our framework can serve as this preliminary evaluation.

## 3. Background and Definitions

### 3.1 Policy

For state space $\mathcal{S}$ and action space $A$, a stochastic policy is denoted $\pi_O(a \mid s)$. We call $\pi_O$ the **Oracle policy**---a black-box policy learned via reinforcement learning, for which no semantic interpretation of the internal representation is provided.

### 3.2 Structurally Constrained Models

A **Surrogate model** is a structurally constrained model that imitates $\pi_O$. It is defined by a function $\phi$ that maps state $s$ to a constrained intermediate representation $z \in Z$ and a function $D$ that outputs an action distribution:

$$z = \phi(s), \qquad \pi_S(a \mid s) = D(\phi(s))$$

Here, $Z$ is a low-dimensional, simple, and interpretable representation space; concrete examples include linear models, depth-limited decision trees, and MoET (Vasic et al., 2019[^3]). This framework is agnostic to the specific implementation of $\pi_S$. Whether one chooses a decision tree, MoET, linear model, or any future interpretable model, they can all be compared on the same evaluation axes of fidelity and invariance. The only requirement is that the model produces outputs compatible with the fidelity metric: discrete action outputs for AA in discrete action spaces, or real-valued action outputs for $R^2$ and $\varepsilon$-agreement in continuous action spaces. In this work, we position the Surrogate model as a tool for identifying structural bottlenecks that measure the preservability of policy behavior.

### 3.3 Explainability Evaluation Framework

In this work, we evaluate the quality of explanations provided by a Surrogate model in two stages.

**Stage 1: Fidelity verification.** If the Surrogate model cannot sufficiently reproduce the behavior of $\pi_O$ on the training distribution, it is not viable as a policy approximation in the first place. The fidelity metric is defined according to the action space type. For discrete action spaces, we use action agreement (AA): $\mathrm{AA}(D) = \mathbb{E}_{s \sim D}[\mathbf{1}[\pi_O(s) = \pi_S(s)]]$. For continuous action spaces, since exact action matching is not directly applicable, AA is redefined as the coefficient of determination ($R^2$); $\varepsilon$-agreement (the rate of convergence within a specified error margin) may be used as a supplementary metric. High values of either metric are a **necessary condition** for the model to serve as a meaningful explanation candidate. As an empirical guideline, we use AA > 0.9 (discrete) or $R^2 > 0.9$ (continuous) as the criterion for high fidelity. However, under extreme physical parameter shifts, these metrics may decline, and this threshold is not intended to be universally achievable across all conditions.

**Stage 2: Invariance testing.** Even a Surrogate model that achieves high AA may, when distilled from a policy containing spurious dependencies, copy that dependency structure wholesale, exhibiting high AA on the training distribution while collapsing under distribution shift. For a distribution shift $D_\text{train} \to D_\text{shift}$, we report the pair $({\rm AA}(D_\text{shift}),\; J_S(D_\text{shift}))$ as the invariance evaluation metric.

Invariance diagnosis is based on the following criteria. A strong suspicion of spurious dependency arises when ${\rm AA}(D_\text{shift}) > \theta_{\rm AA}$ and $J_S(D_\text{shift}) < \alpha \times J_S(D_\text{train})$ hold simultaneously---that is, the Surrogate model continues to reproduce the Oracle policy's actions with high agreement, yet policy performance degrades substantially, suggesting that both depend on spurious features. Conversely, spurious dependency is not indicated when $J_S(D_\text{shift})$ does not exhibit catastrophic collapse even if ${\rm AA}(D_\text{shift})$ decreases. In this paper, we use $\theta_{\rm AA} = 0.9$ and $\alpha = 0.8$. These thresholds are empirical guidelines for the present experimental settings and require adjustment depending on the environment and task.

High invariance does not guarantee the **causal validity** of the dependencies. It remains evidence that the dependencies function effectively within the range of distribution shifts examined. This evaluation framework functions as an empirical diagnostic tool for detecting whether a Surrogate model that achieved high AA has copied spurious dependencies. Note that "invariance" here refers to the maintenance of AA and $J_S$ under distribution shift, and is distinct from the invariance of IRM (Arjovsky et al., 2019[^5]), which aims to learn invariant feature representations.

## 4. Proposed Framework

### 4.1 Training Procedure

We adopt a two-stage training procedure. First, $\pi_O$ is trained using DQN (Mnih et al., 2015[^14]). Then, $\pi_O$ is fixed, and $(s, a)$ pairs collected from its rollouts are used as supervision to distill the Surrogate model via behavioral cloning (Bastani et al., 2018[^6]). By avoiding simultaneous optimization of multiple objectives, the performance of the Surrogate model can be interpreted purely as reproduction capability. Distillation data and evaluation data are collected with independent seeds, measuring generalization of reproduction rather than memorization of the distillation set.

### 4.2 Surrogate Model Candidates

To compare the strength of structural constraints, we position three candidates: a linear model (logistic regression), a depth-limited single decision tree, and MoET. In this study, we primarily use MoET, observing the structural upper bound of fidelity by continuously adjusting the constraint strength through a grid search over the number of experts $K$ and depth $d$. Additionally, Experiments 4 and 5 quantitatively compare all three candidates under identical conditions, examining the effect of structural type on the distribution dependence of AA (see Appendices 1 and 2 for details).

### 4.3 Evaluation Metrics

- **Action Agreement (AA)**: $\mathrm{AA}(D) = \mathbb{E}_{s \sim D}[\mathbf{1}[\pi_O(s) = \pi_S(s)]]$. A metric of fidelity.
- **Policy performance ($J_S$)**: $J_S(D) = \mathbb{E}_{s_0 \sim D,\; \tau \sim \pi_S}\!\left[\sum_{t=0}^{T} r_t\right]$. A metric for invariance evaluation.

## 5. Experiments

### 5.1 Experimental Objectives and Correspondence to Claims

Experiments were designed to empirically validate the following six points. We make explicit which claim each experiment provides evidence for.

1. **Structural constraint strength imposes a structural upper bound on fidelity** (Experiment 1: as a baseline experiment, confirming the relationship between structural constraints and AA).
2. **The state of "high fidelity, low invariance" can be detected in a spurious environment** (Experiment 2: direct evidence for the central claim).
3. **Relatively high invariance can be observed in a spurious-free environment** (Experiment 3: contrastive evidence against Experiment 2).
4. **The type of structure affects fidelity under distribution shift** (Experiments 4 and 5: supplementary evidence. Experiment 6: confirmation that model structure differences originate from structure rather than data volume).
5. **Verifying extensibility to continuous dynamical systems and complex environments** (Experiments 7 and 8: application to LunarLander-v3 and MuJoCo Hopper-v5 and validation of evaluation axis adequacy).
6. **Spurious dependencies that training-distribution faithfulness evaluation (Comprehensiveness faithfulness) cannot detect can be complementarily diagnosed by the proposed framework** (Experiment 9: see Appendix 6).

Each condition was run with 10 random seeds (42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526), and we report mean $\pm$ standard deviation. Distillation data and evaluation data were collected with independent seeds. The type of distribution shift (physical parameter modification vs. reversal of spurious features) was selected based on the nature of the phenomenon to be detected. Formalization of distribution shift selection criteria is left for future work.

### 5.2 Experiment 1: CartPole Noise Augmentation

Independent Gaussian noise of $N \in \{0, 4, 8, 16\}$ dimensions is appended to the CartPole-v1[^18] (Brockman et al., 2016) state (4-dimensional), and DQN[^14] is trained on the augmented state (200,000 steps, with best model saving via EvalCallback). The EvalCallback evaluates the model every 5,000 steps and saves the best-performing model, preventing performance collapse in later stages of DQN training. The Surrogate model uses MoET (all combinations of $K \in \{2, 3, 4\}$ and $d \in \{1, 2, 3, 4, 5\}$). As a baseline experiment without spurious dependencies, we observe the structural upper bound of fidelity imposed by structural constraints.

DQN exhibits large variance in $J$ across seeds, and for some seeds, performance does not reach the criterion ($J \geq 450$) even after EvalCallback (approximately 2 out of 10 seeds). This study is a framework for evaluating the fidelity and invariance of surrogates given a trained oracle; the success or failure of oracle training itself is a precondition for evaluation, not a subject of evaluation. Variance in $J$ across seeds is reported as an oracle performance metric in Table 2 and elsewhere.

### 5.3 Experiment 2: Spurious GridWorld

We design a GridWorld environment where the agent's position $(x, y)$ on a 5$\times$5 grid and a spurious variable $c$ constitute the state, while the goal position is not directly observed. The state space is 3-dimensional ($x, y \in [0,1]$ normalized, $c \in \{0,1\}$), and the action space consists of 4 discrete actions (up, down, left, right). The reward is $+1.0$ upon reaching the goal, with a per-step penalty of $-0.01$, and the episode horizon is 100 steps ($J=-1.000$ corresponds to the cumulative penalty when the goal is not reached and all steps are exhausted). The goal is randomly placed at either $(0,0)$ or $(4,4)$ per episode. The spurious variable $c$ is controlled by the spurious noise probability $p \in \{0.0, 0.2, 0.5\}$: with probability $1-p$, it correctly indicates the goal direction, and with probability $p$, it takes a random value. When $p=0$, $c$ deterministically points to the goal, representing an intentionally strong setting where spurious correlation is maximized. $p=0.2$ and $p=0.5$ are conditions where the reliability of $c$ is partially degraded, designed to introduce variation in the strength of spurious correlation as encountered in real-world settings. The policy learns to depend on $c$ under all $p$ conditions; consequently, manipulating $c$ as a distribution shift causes performance changes. The evaluation conditions are the training distribution (train), a condition where $c$ is randomized (random\_c), and a condition where $c$ is reversed (reversed\_c) (200,000 training steps). All 10 seeds converged for all $p$ conditions ($J_\text{oracle} \approx 0.97$ at $p=0.0$; no seeds were excluded).

### 5.4 Experiment 3: CartPole Physical Parameter Shift

Using a CartPole without spurious features ($N=0$), distribution shift is applied by changing the physical parameters after training. Gravity $g \in \{9.8, 5.0, 20.0\}$ and pole half-length $\ell \in \{0.5, 0.25, 1.0\}$ are varied independently across 5 conditions (train, gravity\_lo, gravity\_hi, pole\_short, pole\_long). The Oracle policy reuses the trained model from Experiment 1 with $N=0$, and the Surrogate model uses the best MoET configuration ($K=4$, $d=5$). The pole\_long condition ($\ell=1.0$) represents a pole length twice that of training, treated as an extreme condition where the Oracle policy itself may cease to function OOD.

### 5.5 Additional Experiments (Experiments 4--9)

Experiments 4--9 were conducted as supplementary validation to reinforce the generality of the evaluation framework established in Experiments 1--3. Detailed settings and results for each experiment are provided in the appendices.

**Experiment 4 (CartPole model comparison; see Appendix 1).** Using the same CartPole noise-augmented environment as Experiment 1 ($N \in \{0, 4, 8, 16\}$), three model types---MoET ($K=4$, $d=5$), single decision tree ($d=5$), and logistic regression---are compared to examine the effect of structural type on AA. 10 seeds, 10,000 distillation samples. At $N=0$, MoET achieved the highest AA (0.915), and the difference from Linear (0.842) was statistically significant ($p_\text{adj}<0.001$).

**Experiment 5 (GridWorld model comparison; see Appendix 2).** Using the same Spurious GridWorld as Experiment 2 ($p \in \{0.0, 0.2, 0.5\}$, evaluation conditions: train / random\_c / reversed\_c), the same three model types are compared. MoET and Tree exhibit nearly identical AA, while Linear tends to be lower across all conditions. In the reversed\_c condition at $p=0.5$, the gap between MoET (0.940) and Linear (0.742) was most pronounced.

**Experiment 6 (Distillation data volume sensitivity analysis; see Appendix 3).** The number of distillation samples $n \in \{1\text{k}, 5\text{k}, 10\text{k}, 20\text{k}\}$ is varied, and MoET, Tree, and Linear are compared in both CartPole ($N=0$) and GridWorld ($p \in \{0.0, 0.5\}$) environments. In the reversed\_c condition of GridWorld $p=0.5$, the AA gap between MoET and Linear persisted even when the data volume was increased 20-fold, confirming that the structural difference originates from model structure rather than data insufficiency.

**Experiment 7 (Extension to LunarLander-v3; see Appendix 4).** We verify whether the framework from the main experiments is applicable to continuous dynamical systems using LunarLander-v3. Against a PPO oracle ($J_\text{oracle}=260\pm13$), distillation is performed with four model types by adding GBT to the three from the main experiments. All 10 seeds converged ($J_\text{oracle}$ range: 238--281; no seeds excluded). Gravity coefficients $g \in \{-10.0, -3.0, -11.5\}$ serve as distribution shift conditions, and evaluation uses AA and $J_S$. GBT achieved AA=0.870$\pm$0.021 and was the only model to exhibit functional policy performance ($J_S=236.8\pm18.8$).

**Experiment 8 (Extension to MuJoCo Hopper-v5; see Appendix 5).** We verify the adequacy of the evaluation axes for continuous action spaces using MuJoCo Hopper-v5. Against a TD3 oracle ($J_\text{oracle}\approx3500$), RegTree at $d \in \{5, 12\}$ confirms structural constraint bottlenecks, and GBT+DAgger is then applied, using $R^2$ and $\varepsilon$-agreement as fidelity metrics with 10 seeds. The Oracle policy is a fixed pretrained TD3 model (RL Zoo); oracle convergence is not applicable, and all 10 distillation seeds completed without failure. Gravity coefficients and friction coefficient scales were used as distribution shift conditions.

**Experiment 9 (Comparison with Comprehensiveness Faithfulness; see Appendix 6).** Comprehensiveness faithfulness (DeYoung et al., 2020[^20])---a widely used training-distribution fidelity evaluation metric---is applied to the same conditions as Experiment 2 (Spurious GridWorld, MoET $K=4,d=5$, 10 seeds) and compared with the invariance evaluation of the proposed framework. Comprehensiveness correctly reflects Oracle's $c$-dependence on the training distribution ($p=0.0$: 0.484; $p=0.5$: 0.103), but cannot predict that $J_S$ collapses catastrophically ($-1.00 \pm 0.00$) under reversed\_c at $p=0.0$. This demonstrates that the invariance evaluation complements the gap left by training-distribution-only evaluation.

### 5.6 Implementation Details and Hyperparameters

The Oracle policy was implemented using stable-baselines3[^19] (Raffin et al., 2021), and the Surrogate model was implemented using scikit-learn (decision trees and linear models), PyTorch (MoET gating layer), and sklearn.ensemble (GBT). All experiments used 10,000 distillation samples as the standard setting (5,000 evaluation samples collected with independent seeds).

**Table A1**: Key hyperparameters of the Oracle policy

| Algorithm | Environment | Key Settings |
|-----------|-------------|--------------|
| DQN | CartPole-v1 | lr=2.3$\times$10$^{-3}$, batch=64, buffer=100k, train\_freq=256, gradient\_steps=128, exploration\_fraction=0.16, 500k steps, EvalCallback (every 5k steps) |
| DQN | Spurious GridWorld | SB3 default, learning\_starts=1,000, 200k steps |
| PPO | LunarLander-v3 | n\_envs=8, rollout n\_steps=1024/env, batch=64, n\_epochs=4, ent\_coef=0.01, 1M steps |
| TD3 | MuJoCo Hopper-v5 | RL Zoo pretrained model (Hopper-v3\_1) |

**Table A2**: Key hyperparameters of the Surrogate model

| Model | Key Settings |
|-------|--------------|
| MoET | $K=4$, $d=5$ (best config), soft gating, Adam lr=1$\times$10$^{-3}$, 100 distillation epochs |
| Single decision tree | DecisionTreeClassifier, max\_depth=5 |
| Linear model | LogisticRegression, C=1.0 (sklearn default) |
| GBT | HistGradientBoostingClassifier, max\_iter=300, lr=0.1, max\_depth=unlimited |
| RegTree (Hopper) | DecisionTreeRegressor, max\_depth=12 (exp011) / 5 (exp012) |
| GBT+DAgger (Hopper) | HistGradientBoostingRegressor (independent per action dim), max\_iter=300, lr=0.1, max\_depth=unlimited; DAgger 10 iterations $\times$ 10,000 samples (110,000 total) |

## 6. Results

### 6.1 Experiment 1: Structural Upper Bound on Fidelity

Adding noise dimensions improves MoET fidelity with depth, but the upper bound decreases. At $N=0$ with $K=4, d=5$, AA=0.915$\pm$0.028; at $N=16$, AA reaches only 0.820$\pm$0.032 (Figure 1). This demonstrates that the achievable upper bound of AA varies with input space complexity. Note: the AA values reported for Experiment 1 are drawn from the exp004 dataset, which uses a unified seed set shared with Experiment 4 (see Appendix 1). An earlier run (exp001) used a separate seed set and yielded AA=0.910$\pm$0.016 at $N=0$, $K=4$, $d=5$; exp004 is the canonical source for both experiments.

![Figure 1: AA heatmap ($K=4$). Rows correspond to $N$, columns to depth $d$.](experiments/results/exp001_cartpole_noise/fig1_aa_heatmap.png)

### 6.2 Experiment 2: Demonstrating High Fidelity with Low Invariance

In Experiment 2 ($p=0.0$), $c$ deterministically encodes the goal direction, so any reasonable learner will acquire a policy dependent on $c$. In this setting, the Surrogate model replicating the $c$ dependency and collapsing under the reversed\_c condition is a consequence by construction. The value of this experiment lies not in demonstrating this consequence but in confirming that the proposed framework's diagnostic criteria function correctly in a controlled setting with a known ground truth.

Under the train condition, AA is high (0.988$\pm$0.011 at the best setting $K=4, d=5$) and $J$ nearly matches. Under the reversed\_c condition, AA remains at 0.942 (95% CI: [0.902, 0.982]) while $J_{\mathrm{oracle}} = J_{\mathrm{surrogate}} = -1.000$, indicating complete collapse (Figure 2). $J_S = -1.000$ was observed without exception across all 10 seeds (zero variance): under the reversed\_c condition, the Surrogate deterministically moves toward the wrong goal, leaving no randomness in the outcome. The AA difference between train and reversed\_c ($\Delta$=0.046) was significant by Welch's $t$-test at $p_\text{adj}=0.030$ ($d=1.14$) (Holm--Bonferroni corrected); note that while significant, the margin is small and should be interpreted with the caveat of $n=10$. Furthermore, the 95% CI lower bound of 0.902 barely exceeds the diagnostic threshold $\theta_{\rm AA}=0.9$ by only 0.002, placing this estimate near the boundary. At $n=10$, Cohen's $d=1.14$, and $\alpha=0.05$, the estimated statistical power is approximately 0.55--0.65, meaning there is a 35--45\% probability of failing to detect a true effect at this sample size. The $J_S$ collapse is a trivially obvious fact confirmed across all seeds and does not rely on statistical testing. Applying the diagnostic criteria from Section 3.3, ${\rm AA}(D_\text{shift}) = 0.942 > \theta_{\rm AA} = 0.9$ and $J_S(D_\text{shift}) = -1.000 \ll \alpha \times J_S(D_\text{train})$, which corresponds to a case with strong suspicion of spurious dependency. This is interpreted as the Surrogate model having directly replicated the Oracle policy's spurious dependency. Under the random\_c condition, AA remains high at 0.965$\pm$0.031, but $J$ stays low for both models. Even when $c$ is randomized, both the Oracle policy and the Surrogate model continue to take actions that depend on the spurious feature $c$, resulting in agreement between their actions but collapse in environmental performance. That is, the random\_c condition also satisfies the spurious dependency detection criteria, demonstrating that the framework can consistently identify this state across multiple types of distribution shift.

When SHAP[^4] (KernelExplainer) is applied to the same Oracle policy, the importance of the spurious feature $c$ is nearly identical between train (Mean $|$SHAP$|$ = 0.0181) and reversed\_c (Mean $|$SHAP$|$ = 0.0178) (Figure 4). SHAP reveals "what the policy depends on" but does not ask "whether that dependency is maintained after distribution shift." Our framework complements this gap through invariance evaluation.

**Visualization of MoET expert trees.** The MoET from Experiment 2 ($p=0.0$, $K=4$, $d=5$, seed=42) was re-distilled, and the expert decision tree structures were extracted. The features are agent\_x, agent\_y $\in [0,1]$ (normalized positions) and $c \in \{0,1\}$ (spurious feature), with 3 dimensions; actions are 0=up, 1=down, 2=left, 3=right (4 values).

    |--- c <= 0.50             # root: first split on spurious feature
    |   |--- agent_y <= 0.12
    |   |   |--- class: 2     # move left (toward goal (0,0), upper-left)
    |   |--- agent_y >  0.12
    |   |   |--- agent_x <= 0.38
    |   |   |   |--- class: 0 # move up
    |   |   |--- agent_x >  0.38
    |   |   |   |--- ...      # left/up movement depending on position
    |--- c >  0.50             # c=1: head toward goal (4,4), lower-right
    |   |--- agent_y <= 0.88
    |   |   |--- agent_x <= 0.62
    |   |   |   |--- ...      # right/down movement depending on position
    |   |   |--- agent_x >  0.62
    |   |   |   |--- class: 1 # move down
    |   |--- agent_y >  0.88
    |   |   |--- class: 3     # move right

The root node's split condition is $c \leq 0.5$, directly revealing from the tree structure that MoET has acquired the spurious feature $c$ as the primary decision criterion for the policy. The subtree for $c=0$ learns guidance behavior toward goal $(0,0)$ (upper-left) with left and up movements, while the subtree for $c=1$ learns guidance behavior toward goal $(4,4)$ (lower-right) with right and down movements. All 4 experts learned an identical tree structure (the gate concentrates on Expert 0), effectively functioning as a single decision tree in this environment. This tree structure directly explains "why AA remains high while $J$ collapses under reversed\_c": the Surrogate model faithfully replicates the Oracle policy's dependence on $c$, and under a distribution where $c$ is reversed, both continue heading toward the wrong goal. Note that the above presents the result for seed=42 as a representative example; the root node $c$-split and identical expert structure were reproduced across all 10 seeds examined.

![Figure 2: GridWorld ($p=0.0$, $K=4$, $d=5$) AA and cumulative reward. Under reversed\_c, $J$ collapses to $-1.000$ while AA remains high.](experiments/results/exp002_spurious_gridworld/fig2_j_shift_p0.png)

### 6.3 Experiment 3: Comparative Observation of Invariance in a Spurious-Free Environment

Table 2 presents the results. The upper rows show the mean $\pm$ standard deviation across all 10 seeds, and the lower rows show statistics for converged seeds only ($J_{\mathrm{oracle}} \geq 450$, 8 seeds). Two of the 10 seeds (seed=2223, 2526) failed to converge due to the stochastic nature of DQN ($J_{\mathrm{oracle}} < 200$); both are reported.

| Evaluation Condition | Seeds | AA | $J_{\mathrm{oracle}}$ | $J_{\mathrm{surrogate}}$ |
|---------------------|-------|-----|-------------|------------|
| train ($g=9.8$, $\ell=0.5$) | 10 | 0.915±0.028 | 428.1±148.5 | 417.9±143.5 |
| train ($g=9.8$, $\ell=0.5$) | 8 (converged) | 0.919±0.029 | 498.4±3.8 | 484.9±26.3 |
| gravity\_lo ($g=5.0$, $\ell=0.5$) | 10 | 0.883±0.049 | 436.5±134.0 | 425.8±120.8 |
| gravity\_lo ($g=5.0$, $\ell=0.5$) | 8 (converged) | 0.901±0.028 | 500.0±0.0 | 474.4±69.6 |
| gravity\_hi ($g=20.0$, $\ell=0.5$) | 10 | 0.861±0.063 | 336.2±180.1 | 347.4±177.7 |
| gravity\_hi ($g=20.0$, $\ell=0.5$) | 8 (converged) | 0.880±0.046 | 390.4±157.5 | 410.0±134.7 |
| pole\_short ($g=9.8$, $\ell=0.25$) | 10 | 0.846±0.115 | 406.8±161.4 | 361.1±156.0 |
| pole\_short ($g=9.8$, $\ell=0.25$) | 8 (converged) | 0.890±0.041 | 477.3±50.5 | 418.2±112.5 |
| pole\_long ($g=9.8$, $\ell=1.0$) | 10 | 0.759±0.078 | 376.5±160.5 | 426.5±133.8 |
| pole\_long ($g=9.8$, $\ell=1.0$) | 8 (converged) | 0.773±0.082 | 447.9±62.4 | 488.7±22.5 |

Across all conditions, both $J_{\mathrm{oracle}}$ and $J_{\mathrm{surrogate}}$ remain at substantially positive values, and no catastrophic collapse comparable to the reversed\_c condition in Experiment 2 ($J=-1.000$) is observed (Figure 3). Applying the diagnostic criteria from Section 3.3, $J_S(D_\text{shift}) \geq \alpha \times J_S(D_\text{train})$ holds for all conditions, none of which meet the criteria for spurious dependency. When restricted to the 8 converged seeds, $J_{\mathrm{oracle}}$ variance decreases substantially (train: 148.5 $\to$ 3.8), and AA generally increases by approximately 0.01--0.04. Variations within this range do not alter the main conclusions. Gravity changes represent a scaling perturbation to the CartPole equations of motion, whereas pole length changes are a qualitatively different perturbation that directly modifies the pendulum's moment of inertia. The observation of similar trends under these two types of perturbation suggests that this characteristic is not an artifact specific to gravity shift. Under gravity\_lo and gravity\_hi, $J_{\mathrm{surrogate}}$ occasionally exceeds $J_{\mathrm{oracle}}$, suggesting a possible regularization effect of distillation.

Under the pole\_long condition ($\ell=1.0$), AA was the lowest across all conditions at 0.759 (0.773 for the 8 converged seeds), and the difference from train was statistically significant (Welch's $t$: $p_\text{adj}=0.0004$, $d=2.65$). Other shift conditions were not significant after Holm--Bonferroni correction (gravity\_hi: $p_\text{adj}=0.087$; gravity\_lo: $p_\text{adj}=0.186$; pole\_short: $p_\text{adj}=0.186$). The reversal where $J_{\mathrm{oracle}}=376.5$ versus $J_{\mathrm{surrogate}}=426.5$ indicates that the Surrogate model behaves more adaptively than the Oracle policy in response to changes in pole length. The interpretation of this reversal phenomenon is discussed in Section 8.

![Figure 3: Comparison. Left column (spurious environment): $J$ collapses while AA remains high. Right column (spurious-free): $J$ remains at substantially positive values across multiple shifts.](experiments/results/exp003_cartpole_gravity/fig3_diagnostic_comparison.png)

![Figure 4: SHAP feature importance ($p=0.0$). The importance of $c$ is nearly identical between train and reversed\_c, indicating failure to detect dependency collapse.](experiments/results/exp002_spurious_gridworld/fig4_shap_p0.png)


## 7. Discussion

The central claim of this framework is that faithfulness does not imply validity. While it is structurally obvious that behavioral cloning will replicate spurious dependencies, the core issue is that this replication is invisible in the AA metric. As Experiment 2 demonstrated, when spurious correlations exist, the Surrogate model replicates the erroneous dependency and achieves high AA on the training distribution while both models fail under distribution shift. Only by adding invariance evaluation---observing the pair $({\rm AA}(D_\text{shift}),\; J_S(D_\text{shift}))$---can this state be identified from numerical indicators. Experiment 3 confirmed as a contrast that the same framework does not exhibit catastrophic collapse in a spurious-free environment. The contribution of this work lies not in pointing out that replication occurs, but in providing a framework for detecting it quantitatively and systematically.

IRM (Arjovsky et al., 2019[^5]) and related invariant learning research aim to eliminate spurious dependencies during training. Our framework differs in that it does not alter training strategies and can be applied post hoc to any pair of a trained policy and a trained Surrogate model. As a practical implication, our framework can be utilized simply by adding evaluation under distribution shift to existing distillation-based XRL systems.

Formal statistical testing via Welch's $t$-test (Holm--Bonferroni correction) was conducted for the main claims (details in `experiments/results/pvalue_summary.csv`). The difference between train and reversed\_c in Experiment 2 was significant for AA at $p_\text{adj}=0.030$ ($d=1.14$), statistically supporting the core claim of spurious detection. The $J_S$ collapse was $-1.000$ across all 10 seeds (zero variance) and is trivially obvious without statistical testing. The robustness of the diagnostic criteria to threshold choice is addressed by sensitivity analysis (Tables 6 and 7, later in this section), confirming that qualitative conclusions remain unchanged across all threshold values tested. In Experiment 3 (non-spurious), the overall trend showed no catastrophic collapse of $J$, with only the AA decline under the pole\_long condition being significant ($p_\text{adj}=0.0004$, $d=2.65$).

The model comparisons in Experiments 4 and 5 (see Appendices 1 and 2) showed a tendency for tree-structured models to maintain fidelity under distribution shift more stably than linear models. However, since statistically significant differences after multiple testing correction were confirmed only under a subset of conditions, caution is required in generalizing this tendency. The sensitivity analysis in Experiment 6 (see Appendix 3) reinforces this tendency, showing that the AA gap between MoET and Linear in the reversed\_c condition of GridWorld $p=0.5$ was not resolved even when the distillation data was increased 20-fold. The similar behavior of Tree and MoET suggests that the branching structure of the trees themselves, rather than MoET's gating layer, may be the key to fidelity. However, the diagnostic demonstration in Experiment 2 requires AA under distribution shift to exceed $\theta_{\rm AA}=0.9$; Tree falls below this threshold (reversed\_c AA=0.887), whereas MoET $K=4, d=5$ consistently maintains higher AA, which is why it was selected as the primary surrogate. Note that Tree would also pass the criterion if $\theta_{\rm AA}$ were set to 0.85, as confirmed by the sensitivity analysis (Table 6).

SHAP is useful in showing "which features the current policy depends on," but cannot address whether those dependencies are maintained under environmental changes. The invariance evaluation in this work does not replace SHAP but complements it by providing information that SHAP alone cannot reveal---the validity of the dependencies. The comparison with Comprehensiveness faithfulness (DeYoung et al., 2020[^20]) in Appendix 6 quantitatively demonstrates that while Comprehensiveness captures within-training-distribution feature reliance, the invariance evaluation proposed here provides complementary diagnosis of whether that reliance remains valid after distribution shift.

The arbitrariness of the AA > 0.9 threshold is addressed through sensitivity analysis by varying the threshold to 0.85, 0.90, and 0.95. Table 6 shows the mean AA for key conditions and pass/fail judgments for each threshold.

**Table 6**: AA threshold sensitivity analysis (key conditions)

| Experiment | Evaluation Condition | AA (mean) | > 0.85 | > 0.90 | > 0.95 |
|------------|---------------------|-----------|--------|--------|--------|
| Experiment 3 (CartPole) | train (all 10) | 0.915 | ✓ | ✓ | — |
| Experiment 3 (CartPole) | train (converged 8) | 0.919 | ✓ | ✓ | — |
| Experiment 3 (CartPole) | gravity\_lo (all 10) | 0.883 | ✓ | — | — |
| Experiment 3 (CartPole) | gravity\_lo (converged 8) | 0.901 | ✓ | ✓ | — |
| Experiment 3 (CartPole) | gravity\_hi (all 10) | 0.861 | ✓ | — | — |
| Experiment 3 (CartPole) | gravity\_hi (converged 8) | 0.880 | ✓ | — | — |
| Experiment 3 (CartPole) | pole\_short (all 10) | 0.846 | ✓ | — | — |
| Experiment 3 (CartPole) | pole\_short (converged 8) | 0.890 | ✓ | — | — |
| Experiment 3 (CartPole) | pole\_long (all 10) | 0.759 | — | — | — |
| Experiment 3 (CartPole) | pole\_long (converged 8) | 0.773 | — | — | — |
| Experiment 2 (GridWorld, $p=0.0$) | train | 0.988 | ✓ | ✓ | ✓ |
| Experiment 2 (GridWorld, $p=0.0$) | reversed\_c | 0.942 | ✓ | ✓ | — |

Regardless of whether the threshold is set to 0.85, 0.90, or 0.95, the qualitative conclusions remain unchanged. Using AA > 0.9 as an empirical guideline for "high action agreement" is justified within the scope of the present data.

A similar sensitivity check was conducted for the arbitrariness of $\alpha=0.8$. Table 7 shows the detection results when $\alpha \in \{0.7, 0.8, 0.9\}$ is varied.

**Table 7**: $\alpha$ sensitivity analysis ($J_S(D_\text{shift}) / J_S(D_\text{train})$ and detection results)

| Experiment | Evaluation Condition | AA | $J_S / J_\text{train}$ | $\alpha=0.7$ | $\alpha=0.8$ | $\alpha=0.9$ |
|------------|---------------------|----|----------------------|-------------|-------------|-------------|
| Experiment 2 ($p=0.0$) | reversed\_c | 0.942 | −1.03 | detected | detected | detected |
| Experiment 2 ($p=0.0$) | random\_c | 0.965 | 0.06 | detected | detected | detected |
| Experiment 3 (non-spurious) | gravity\_hi | 0.861 | 0.83 | — | — | — |
| Experiment 3 (non-spurious) | pole\_short | 0.846 | 0.86 | — | — | — |
| Experiment 3 (non-spurious) | gravity\_lo | 0.883 | 1.02 | — | — | — |
| Experiment 7 (LunarLander, GBT) | gravity\_hi | 0.878 | 0.87 | — | — | — |
| Experiment 7 (LunarLander, GBT) | gravity\_lo | 0.712 | 0.58 | — | — | — |

Detection requires both conditions to hold: "$\mathrm{AA}(D_\text{shift}) > \theta_{\mathrm{AA}}$ and $J_S(D_\text{shift}) < \alpha \times J_S(D_\text{train})$." The shift conditions in Experiments 3 and 7 all have $\mathrm{AA} < \theta_{\mathrm{AA}} = 0.9$, so they are not detected regardless of $\alpha$. In particular, gravity\_lo in Experiment 7 shows $J_S$ ratio = 0.58, declining to a level close to the threshold, but is not detected because the AA condition is not met. Thus, detection is determined by the joint condition of $J_S$ ratio and AA, not by $J_S$ ratio alone. In the present dataset, there is a large separation between the $J_S$ ratios of spurious conditions ($-1.03$, $0.06$) and non-spurious conditions ($0.58$--$1.02$), and the qualitative conclusions remain unchanged for any $\alpha \in \{0.7, 0.8, 0.9\}$. $\alpha=0.8$ is justified as a conservative midpoint.

Detection of spurious dependencies becomes practically meaningful only when combined with subsequent remedial actions. Our framework specializes in detection and does not provide remediation itself, but the detection results suggest subsequent actions such as: removing spurious features from the observation space, redesigning the environment's reward function or state space to eliminate spurious correlations, or retraining the Oracle policy using invariant learning methods such as IRM. Which action is optimal depends on the nature of the environment and task and has not been empirically evaluated within the scope of this study, but the detection results are intended to serve as the starting point for subsequent debugging and improvement cycles.

The essential contribution of this work lies not in proposing a specific explainability method but in providing an **evaluation methodology for explanation quality** of RL policies. The choice of which Surrogate model to use is left to the researcher or practitioner, and this framework provides a common basis for quantitatively evaluating that choice. By numerically answering two questions---"Does an explanation candidate exist? (fidelity)" and "Are the dependencies captured by that explanation valid within the examined range? (invariance)"---this work aims to establish an evaluation foundation that supports cycles of comparison, selection, and improvement of explanation methods in XRL.

## 8. Limitations

This framework has four specific limitations.

First, the main experiments are limited to CartPole and GridWorld, which are small-scale discrete control environments. Experiment 7 (see Appendix 4) showed that a GBT Surrogate model achieved AA = 0.870 with functional policy performance ($J_S = 237$), demonstrating the framework's extensibility to continuous dynamical systems. Experiment 8 (see Appendix 5) demonstrated that GBT+DAgger achieved $R^2 = 0.968 \pm 0.004$ on MuJoCo Hopper-v5, passing Stage 1 ($R^2 > 0.9$), while simultaneously achieving $J_S$ at 99.7\% of the oracle---confirming that Stage 1 passage and functional policy performance can be achieved simultaneously in continuous action spaces. Under distribution shift, $R^2$ declined substantially (gravity\_hi: 0.326, gravity\_lo: 0.056), which the framework detected. Additionally, the $J_\text{surrogate} > J_\text{oracle}$ reversal observed under the pole\_long condition (CartPole Experiment 3) and the gravity\_lo condition (Hopper Experiment 8) is intriguing as a regularization effect of distillation, but elucidating its mechanism is left for future work.

Second, the statistical reliability of each condition is based on 10 random seeds, and particularly under the pole\_short condition (AA standard deviation 0.115), variability remains in post-shift behavior. Welch's $t$-tests (Holm--Bonferroni correction) were conducted for the main comparisons, confirming statistical support for the central claim (Experiment 2 spurious detection) and the significant AA decline under pole\_long, but significant differences were not confirmed after correction for the pole\_short and gravity conditions (gravity\_hi: $p_\text{adj}=0.087$; gravity\_lo and pole\_short: $p_\text{adj}=0.186$). Caution is required in interpreting these comparisons.

Third, the framework assumes that the Oracle policy operates on the evaluation distribution. In our experiments, the Oracle policy still functioned under the pole\_long condition with $J_{\mathrm{oracle}}=376.5$, and a reversal was observed where the Surrogate model achieved $J_{\mathrm{surrogate}}=426.5$. This reversal suggests a regularization effect of distillation (compression into a simpler structure aids generalization after shift), but elucidating the mechanism is left for future work. Under conditions where the Oracle policy fails OOD, it becomes impossible to distinguish whether the decline in AA is due to the Surrogate model's lack of invariance or an inevitable divergence accompanying Oracle policy failure, requiring caution.

Fourth, the choice of distribution shifts (gravity, pole length, reversal of $c$) is arbitrary, and what shifts are chosen can affect invariance evaluation results. In real-world applications, "what to shift" is not self-evident and constitutes a practical question when applying this framework. Feature importance methods such as SHAP[^4] provide cues for prioritizing features with high dependency as targets for shift operations, and IRM[^5] can be applied for preliminary narrowing of spurious candidates when multiple training environments are available. However, these aid the exploration of shift candidates, and formalization of comprehensive selection criteria remains a topic for future work.

## 9. Conclusion

This work proposed a framework that evaluates the explainability of reinforcement learning policies along two axes: fidelity (action agreement on the training distribution) and invariance (maintenance of AA and $J_S$ under distribution shift). Through the decoupling design---deploying a Surrogate model post hoc without modifying the Oracle policy---the framework circumvents the explainability-performance trade-off while enabling comparison of arbitrary interpretable models on common evaluation axes.

Through experiments using CartPole and Spurious GridWorld, we demonstrated that the state of "high fidelity, low invariance"---maintaining high AA while collapsing under distribution shift---can be identified from numerical indicators. Tree-structured models showed a tendency to maintain fidelity under distribution shift more stably than linear models, though statistically significant differences were limited to a subset of conditions. Extension to LunarLander-v3 (Experiment 7; Appendix 4) showed that a GBT Surrogate model achieved AA = 0.870, and extension to MuJoCo Hopper-v5 (Experiment 8; Appendix 5) showed that GBT+DAgger distillation achieved $R^2 = 0.968$ and $J_S$ at 99.7\% of the oracle, confirming that Stage 1 passage and functional policy performance can be simultaneously achieved in continuous action spaces. Under distribution shift, the framework detected substantial degradation in $R^2$ (gravity\_hi: 0.326, gravity\_lo: 0.056).

Future work includes application to high-dimensional observation spaces, increasing the number of seeds for greater statistical reliability, and formalizing distribution shift selection criteria. Regarding full-scale application to continuous action environments, the evaluation pipeline itself is applicable to continuous action spaces (including redefinition of AA via $\varepsilon$-agreement), and Experiment 8's GBT+DAgger provides one such example. Extension to more complex continuous control tasks and high-dimensional observation spaces remains future work. Furthermore, generating rule sequences or natural language explanations from Surrogate model structures and examining how these correspond to invariance would be the next step toward practical explainability.

[^1]: Chen, R., et al. (2022). Machine explanations and human understanding. *Transactions on Machine Learning Research*.

[^2]: Mindlin, D., et al. (2025). Towards co-constructed explanations. *International Conference on Human-Agent Interaction*.

[^3]: Vasic, M., et al. (2019). MoET: Interpretable and verifiable reinforcement learning via mixture of expert trees. *AAAI*.

[^4]: Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.

[^5]: Arjovsky, M., et al. (2019). Invariant risk minimization. *arXiv:1907.02893*.

[^6]: Bastani, O., Pu, Y., & Solar-Lezama, A. (2018). Verifiable reinforcement learning via policy extraction. *Advances in Neural Information Processing Systems (NeurIPS)*.

[^7]: Kolter, J. Z., & Ng, A. Y. (2009). Regularization and feature selection in least-squares temporal difference learning. *International Conference on Machine Learning (ICML)*.

[^8]: Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why should I trust you?": Explaining the predictions of any classifier. *Proceedings of the ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD)*.

[^9]: Alvarez-Melis, D., & Jaakkola, T. S. (2018). Towards robust interpretability with self-explaining neural networks. *Advances in Neural Information Processing Systems (NeurIPS)*.

[^10]: Samek, W., Wiegand, T., & Müller, K.-R. (2017). Explainable artificial intelligence: Understanding, visualizing and interpreting deep learning models. *arXiv:1708.08296*.

[^11]: Koh, P. W., et al. (2020). Concept bottleneck models. *International Conference on Machine Learning (ICML)*.

[^12]: Greydanus, S., Koul, A., Dodge, J., & Fern, A. (2018). Visualizing and understanding Atari agents. *International Conference on Machine Learning (ICML)*.

[^13]: Yuksekgonul, M., Wang, M., Slack, D., Singh, S., Guestrin, C., & Lakkaraju, H. (2023). Post-hoc concept bottleneck models. *International Conference on Learning Representations (ICLR)*.

[^14]: Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. *Nature*, 518, 529–533.

[^15]: Gulrajani, I., & Lopez-Paz, D. (2021). In search of lost domain generalization. *International Conference on Learning Representations (ICLR)*.

[^16]: Sagawa, S., Koh, P. W., Hashimoto, T. B., & Liang, P. (2020). Distributionally robust neural networks for group shifts: On the importance of regularization for worst-case generalization. *International Conference on Learning Representations (ICLR)*.

[^17]: Puiutta, E., & Veith, E. M. S. P. (2020). Explainable reinforcement learning: A survey. *International Cross-Domain Conference for Machine Learning and Knowledge Extraction (CD-MAKE)*.

[^18]: Brockman, G., et al. (2016). OpenAI Gym. *arXiv:1606.01540*.

[^19]: Raffin, A., et al. (2021). Stable-baselines3: Reliable reinforcement learning implementations. *Journal of Machine Learning Research*, 22(268), 1–8.

[^20]: DeYoung, J., et al. (2020). ERASER: A benchmark to evaluate rationalized NLP models. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL)*.

---

## Appendices

### Appendix 1. Experiment 4: CartPole Model Comparison

**Experimental setup.** Using the same CartPole noise-augmented environment as Experiment 1 ($N \in \{0, 4, 8, 16\}$), three model types---MoET ($K=4$, $d=5$), single decision tree ($d=5$), and logistic regression---are compared. 10,000 distillation samples, 5,000 evaluation samples, AA reported over 10 seeds.

**Results.** Table A3 shows AA for each $N$ (mean $\pm$ standard deviation over 10 seeds).

**Table A3**: CartPole model comparison (AA)

| $N$ | MoET | Tree | Linear |
|-----|------|------|--------|
| 0  | 0.915±0.028 | 0.902±0.031 | 0.842±0.033 |
| 4  | 0.881±0.035 | 0.858±0.043 | 0.857±0.054 |
| 8  | 0.852±0.050 | 0.812±0.065 | 0.846±0.060 |
| 16 | 0.820±0.032 | 0.768±0.046 | 0.830±0.037 |

At $N=0$, MoET achieved the highest AA (0.915), followed by Tree (0.902). Linear was lower at 0.842 compared to the other two. At $N=4$ and $8$, MoET still maintains superiority but the gap narrows. At $N=16$, Linear (0.830) numerically exceeds MoET (0.820), but this difference is not significant after correction ($p_\text{adj}=0.54$). Welch's $t$-test (Holm--Bonferroni correction, 12 total comparisons) showed that at $N=0$, both MoET and Tree had significantly higher AA than Linear (MoET vs Linear: $p_\text{adj}<0.001$, $d=2.39$; Tree vs Linear: $p_\text{adj}<0.01$, $d=1.90$), while the difference between MoET and Tree was not significant ($p_\text{adj}=0.36$). At $N=16$, Linear significantly exceeded Tree ($p_\text{adj}=0.037$, $d=1.50$), indicating that linear models exhibit higher fidelity than tree structures under high-noise conditions. At $N=4$ and $8$, no differences were significant (all $p_\text{adj}>0.4$). Note: the correction family was defined as all 12 comparisons (3 pairwise model comparisons × 4 $N$-levels) treated jointly (see `pvalue_summary.csv`). Defining separate 3-comparison families per $N$-level would also be defensible, but we adopted the more conservative global correction for transparency.

### Appendix 2. Experiment 5: GridWorld Model Comparison

**Experimental setup.** Using the same Spurious GridWorld as Experiment 2 ($p \in \{0.0, 0.2, 0.5\}$, evaluation conditions: train / random\_c / reversed\_c), MoET, Tree, and Linear are compared.

**Results.** Table A4 shows AA for $p \in \{0.0, 0.2, 0.5\}$.

**Table A4**: GridWorld model comparison (AA)

| $p$ | Evaluation Condition | MoET | Tree | Linear |
|-----|---------------------|------|------|--------|
| 0.0 | train       | 0.985±0.014 | 0.971±0.012 | 0.903±0.052 |
| 0.0 | random\_c   | 0.958±0.035 | 0.930±0.044 | 0.836±0.079 |
| 0.0 | reversed\_c | 0.930±0.063 | 0.887±0.084 | 0.771±0.133 |
| 0.2 | train       | 0.996±0.003 | 0.990±0.009 | 0.971±0.021 |
| 0.2 | random\_c   | 0.959±0.100 | 0.931±0.107 | 0.920±0.048 |
| 0.2 | reversed\_c | 0.922±0.200 | 0.872±0.211 | 0.867±0.102 |
| 0.5 | train       | 0.999±0.001 | 0.998±0.001 | 0.878±0.100 |
| 0.5 | random\_c   | 0.970±0.064 | 0.971±0.065 | 0.811±0.146 |
| 0.5 | reversed\_c | 0.940±0.132 | 0.942±0.133 | 0.742±0.220 |

MoET and Tree exhibit nearly identical AA, while Linear tends to be lower across all conditions. Welch's $t$-test (Holm--Bonferroni correction, 27 total comparisons) found only 2 comparisons significant after correction, both in the $p=0.0$ condition for MoET vs Linear (train: $p_\text{adj}=0.019$, $d=2.13$; random\_c: $p_\text{adj}=0.018$, $d=2.00$). Under the multiple testing correction across 27 comparisons, the majority of differences did not meet the criterion for statistical significance. While a tendency for tree-structured models to maintain fidelity under distribution shift more stably than linear models was observed, it should be noted that statistically significant differences were not widely confirmed. The difference between MoET and Tree was not significant under any condition (all $p_\text{adj}>0.5$), and the similarity in their behavior is statistically supported.

The high standard deviations in the $p=0.2$ reversed\_c condition (MoET: AA=0.922±0.200) and $p=0.5$ reversed\_c condition (AA=0.940±0.132) warrant clarification regarding threshold-based diagnostics. Per-seed inspection shows that 9 of 10 seeds at $p=0.2$ (median 0.996, IQR 0.984--0.998) and 8 of 10 seeds at $p=0.5$ (median 0.998, IQR 0.962--0.999) achieved AA > 0.9. The large standard deviations stem from a small number of outlier seeds in which the policy did not strongly acquire the spurious dependency; by median-based assessment, high-AA dependency replication is stably observed.

### Appendix 3. Experiment 6: Distillation Data Volume Sensitivity Analysis

**Experimental setup.** The number of distillation samples $n \in \{1\text{k}, 5\text{k}, 10\text{k}, 20\text{k}\}$ is varied, and MoET, Tree, and Linear are compared in both CartPole ($N=0$) and GridWorld ($p \in \{0.0, 0.5\}$) environments.

**Results.** Table A5 shows the results for CartPole ($N=0$).

**Table A5**: Distillation data volume sensitivity analysis (CartPole $N=0$, AA)

| $n$ | MoET | Tree | Linear |
|-----|------|------|--------|
| 1k  | 0.888±0.020 | 0.881±0.028 | 0.823±0.051 |
| 5k  | 0.916±0.024 | 0.904±0.028 | 0.839±0.034 |
| 10k | 0.915±0.028 | 0.903±0.031 | 0.842±0.033 |
| 20k | 0.926±0.022 | 0.906±0.031 | 0.844±0.033 |

MoET and Tree reach near-saturation of AA from 5k onward, while Linear increases gradually with data volume but remains at 0.844 even at 20k. In the reversed\_c condition of GridWorld $p=0.5$, the AA gap between MoET and Linear (approximately 0.22) persists even with a 20-fold increase in data volume (Welch's $t$-test $p_\text{adj}<0.01$), indicating that the difference in fidelity under distribution shift originates from model structure rather than distillation data insufficiency (Figure 5).

![Figure 5: AA vs. distillation sample size for GridWorld (p=0.5). Under the reversed_c condition, the gap between MoET/Tree and Linear is structurally fixed regardless of data volume.](experiments/results/exp006_distill_sensitivity/sensitivity_gridworld_p05.png)

### Appendix 4. Experiment 7: Extension to LunarLander-v3

**Experimental setup.** Against a LunarLander-v3 PPO oracle ($J_\text{oracle}=260\pm13$), distillation is performed with four model types: MoET, Tree, Linear, and GBT. Gravity coefficients $g \in \{-10.0, -3.0, -11.5\}$ serve as distribution shift conditions. Each is evaluated over 10 seeds.

**Results.** Table A6 shows AA and $J_S$ under training and distribution shift conditions.

**Table A6**: LunarLander-v3 Experiment 7 results (mean $\pm$ standard deviation over 10 seeds)

| Model | AA (train) | AA (gravity\_lo) | AA (gravity\_hi) | $J_S$ (train) | $J_S$ (gravity\_lo) | $J_S$ (gravity\_hi) |
|-------|-----------|-----------------|-----------------|--------------|--------------------|--------------------|
| **GBT** | **0.870 ± 0.021** | 0.712 ± 0.063 | **0.878 ± 0.018** | **236.8 ± 18.8** | 137.8 ± 39.1 | **205.9 ± 25.3** |
| Linear | 0.767 ± 0.046 | 0.713 ± 0.078 | 0.803 ± 0.032 | 178.3 ± 72.2 | 200.0 ± 30.5 | 157.7 ± 76.9 |
| MoET   | 0.732 ± 0.026 | 0.547 ± 0.080 | 0.769 ± 0.029 | −264.1 ± 90.2 | −301.3 ± 122.3 | −280.6 ± 106.6 |
| Tree   | 0.711 ± 0.034 | 0.554 ± 0.087 | 0.752 ± 0.033 | −293.8 ± 104.0 | −316.3 ± 169.4 | −293.2 ± 114.2 |

GBT achieved AA = 0.870 $\pm$ 0.021, substantially exceeding MoET (0.732), Tree (0.711), and Linear (0.767). Moreover, only GBT and Linear successfully landed ($J_S > 0$); MoET and Tree failed to function as policies ($J_S \ll 0$) despite having AA of approximately 0.72. This result demonstrates that the difference in AA has a critical impact on policy performance.

Under distribution shift, GBT maintained nearly equivalent performance to the training condition under gravity\_hi ($g = -11.5$, +15% relative to training): AA = 0.878 $\pm$ 0.018 and $J_S = 206 \pm 25$. Under gravity\_lo ($g = -3.0$, lunar-equivalent), both AA and $J_S$ declined simultaneously: AA = 0.712 $\pm$ 0.063 and $J_S = 138 \pm 39$. The AA decline of GBT under gravity\_lo ($\Delta$=0.158) was significant by Welch's $t$-test at $p_\text{adj}<0.001$ ($d=3.36$), and the $J_S$ decline ($\Delta$=99) was also significant at $p_\text{adj}<0.001$ ($d=3.23$) (Holm--Bonferroni corrected). Applying the diagnostic criteria from Section 3.3, $\mathrm{AA}(D_\text{shift}) < \theta_{\mathrm{AA}} = 0.9$ for all conditions, so spurious dependency is not indicated. This degradation pattern is consistent with the "expected post-shift degradation" observed in the CartPole physical parameter shift (Experiment 3) in a non-spurious environment.

### Appendix 5. Experiment 8: Extension to MuJoCo Hopper-v5

**Experimental setup.** Against a MuJoCo Hopper-v5 TD3 oracle ($J_\text{oracle}\approx3500$), regression-type Surrogate models are applied. $R^2$ and $\varepsilon$-agreement ($\|\hat{a} - a\|_2 < 0.2$) are used as fidelity metrics, evaluated over 10 seeds. Distribution shift conditions include gravity coefficients $g \in \{-9.81, -5.0, -20.0\}$ and foot contact friction coefficient scales $f \in \{0.7, 1.3\}$.

**Structural constraint bottleneck (BC).** We first confirmed the effect of structural constraints using RegTree with behavioral cloning (BC). Restricting depth to $d=5$ yielded $R^2 = 0.698 \pm 0.009$, while relaxing to $d=12$ achieved $R^2 = 0.922 \pm 0.008$. This confirms the existence of a "structural constraint bottleneck" in continuous environments (replication of Claim 1). However, under BC distillation, covariate shift caused $J_S$ to remain at approximately 5% of the oracle, making it insufficient as a basis for invariance evaluation.

**Simultaneous achievement of both criteria via GBT+DAgger.** To correct BC's covariate shift, GBT+DAgger (Dataset Aggregation) was applied. At each iteration, the oracle relabels the state distribution visited by the surrogate, repeated 10 times (initial 10,000 samples + 10,000 additional samples per iteration, totaling 110,000 samples). GBT+DAgger achieved $R^2 = 0.968 \pm 0.004$, clearly passing Stage 1 ($R^2 > 0.9$), while simultaneously reaching $J_S = 3527 \pm 25$ (99.7\% of oracle; Table A7).

**Table A7**: GBT+DAgger Surrogate, train condition (Hopper-v5, mean $\pm$ standard deviation over 10 seeds)

| Method | $R^2$ (train) | $\mathrm{AA}_\varepsilon$ ($\varepsilon=0.2$) | $J_S$ | $J_S / J_\text{oracle}$ |
|--------|--------------|----------------------------------------------|-------|------------------------|
| GBT+DAgger | **0.968 ± 0.004** | 0.808 ± 0.019 | **3527 ± 25** | 99.7 % |

**Invariance evaluation under distribution shift.** Table A8 shows results under distribution shift conditions.

**Table A8**: GBT+DAgger Surrogate under distribution shift (mean $\pm$ standard deviation over 10 seeds)

| Condition | $R^2$ | $\mathrm{AA}_\varepsilon$ | $J_S$ | $J_\text{oracle}$ | $J_S / J_\text{oracle}$ |
|-----------|-------|--------------------------|-------|-------------------|------------------------|
| train | 0.968 ± 0.004 | 0.808 ± 0.019 | 3527 ± 25 | 3536 | 99.7 % |
| gravity\_hi ($g=-20$) | 0.326 ± 0.084 | 0.069 ± 0.019 | 299 ± 19 | 308 | 97.1 % |
| gravity\_lo ($g=-5$) | 0.056 ± 0.097 | 0.056 ± 0.011 | 678 ± 479 | 389 | 174 % |
| friction\_hi ($f=1.3$) | 0.674 ± 0.032 | 0.281 ± 0.026 | 1110 ± 139 | 1403 | 79.1 % |
| friction\_lo ($f=0.7$) | 0.505 ± 0.037 | 0.189 ± 0.014 | 1011 ± 241 | 1121 | 90.2 % |

Under gravity\_hi and gravity\_lo, $R^2$ declined to 0.326 and 0.056 respectively, representing substantial loss of the high fidelity achieved at training ($R^2=0.968$). The framework detected this degradation along both the $R^2$ and $J_S$ axes (replication of Claim 3). Under gravity\_lo, $J_S = 678 \pm 479$ (174\% of oracle) shows a tendency toward the $J_\text{surrogate} > J_\text{oracle}$ reversal consistent with the pole\_long condition in CartPole Experiment 3. However, the large standard deviation ($\pm$479) means this reversal is not statistically conclusive. Friction shifts showed moderate $R^2$ degradation (0.505--0.674) with relatively maintained $J_S$. This experiment confirms that the two-axis evaluation logic of fidelity and invariance applies consistently in continuous action spaces.

---

### Appendix 6. Comparison with Comprehensiveness Faithfulness (Experiment 9)

**Purpose.** We apply Comprehensiveness faithfulness---a widely used training-distribution fidelity evaluation metric---to the same experiments and demonstrate its complementarity with the proposed invariance evaluation.

**Definition of Comprehensiveness.** Following DeYoung et al. (2020), we define the Comprehensiveness of feature $i$ as:

$$\mathrm{comp}_i = \mathrm{AA}(\text{all features}) - \mathrm{AA}(\text{feature } i \text{ masked to mean})$$

A larger $\mathrm{comp}_i$ indicates that the Surrogate model more strongly depends on feature $i$ within the training distribution.

**Experimental setup.** We reuse the exp002 oracle models (all $p$ values, all seeds) and re-distill Surrogate models under identical settings (MoET $K=4, d=5$, 10,000 distillation samples) to compute $\mathrm{comp}_c$ for the spurious feature $c$. Results are placed alongside the existing invariance evaluation (reversed\_c condition from exp002).

**Table A9**: Comprehensiveness vs. Invariance Evaluation (Spurious GridWorld, MoET $K=4,d=5$, mean±SD across 10 seeds)

| $p$ | $\mathrm{comp}_c$ | $\mathrm{comp}_x$ | $\mathrm{comp}_y$ | $\mathrm{AA}_\text{train}$ | $\mathrm{AA}_\text{rev\_c}$ | $J_S^\text{rev\_c}$ |
|-----|-------------------|-------------------|-------------------|----------------------------|-----------------------------|--------------------|
| 0.0 | **0.484±0.013** | 0.316±0.070 | 0.324±0.069 | 0.985±0.014 | 0.942±0.056 | **−1.00±0.00** |
| 0.2 | 0.303±0.098 | 0.582±0.228 | 0.593±0.154 | 0.996±0.003 | 0.929±0.201 | **−1.00±0.00** |
| 0.5 | 0.103±0.099 | 0.600±0.249 | 0.392±0.178 | 0.999±0.001 | 0.940±0.132 | −0.30±0.31 |

**Interpretation.** $\mathrm{comp}_c$ decreases monotonically with $p$, correctly reflecting the oracle's degree of $c$-dependence on the training distribution. At $p=0.0$, $\mathrm{comp}_c = 0.484$ substantially exceeds the position features ($\mathrm{comp}_x = 0.316$, $\mathrm{comp}_y = 0.324$), confirming that the surrogate depends most strongly on $c$.

However, because Comprehensiveness is a training-distribution metric, it has no means of determining whether this dependency is spurious or causal. At $p=0.0$, despite the high $\mathrm{comp}_c$, policy performance under reversed\_c collapses to $J_S = -1.00$ uniformly across all 10 seeds. Comprehensiveness informs us that "the surrogate depends on $c$" but cannot warn that "this dependency will fail catastrophically under distribution shift." The invariance evaluation proposed in this framework---$\mathrm{AA}_\text{rev\_c}$ and $J_S^\text{rev\_c}$---directly measures this gap and empirically demonstrates the consequences of spurious dependency.

**Conclusion on complementarity.** Comprehensiveness and invariance evaluation are not competing but complementary. Comprehensiveness quantifies *what* the surrogate uses and *how strongly* on the training distribution; invariance evaluation diagnoses *whether* that usage remains valid after distribution shift. Combining both axes enables more complete assessment of surrogate explanation quality.
