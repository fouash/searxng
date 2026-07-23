// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  absDependencies,
  addDependencies,
  create,
  divideDependencies,
  eDependencies,
  evaluateDependencies,
  expDependencies,
  factorialDependencies,
  gcdDependencies,
  lcmDependencies,
  log1pDependencies,
  log2Dependencies,
  log10Dependencies,
  logDependencies,
  modDependencies,
  multiplyDependencies,
  nthRootDependencies,
  piDependencies,
  powDependencies,
  roundDependencies,
  signDependencies,
  sqrtDependencies,
  subtractDependencies
} from "mathjs/number";
import { Plugin } from "../Plugin.ts";
import { appendAnswerElement } from "../util/appendAnswerElement.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Parses and solves mathematical expressions using mathjs library.
 *
 * Supports:
 * - Basic arithmetic: +, -, *, /, %
 * - Functions: sin, cos, tan, abs, sqrt, pow, etc.
 * - Constants: pi, e, phi
 * - Bitwise operations: gcd, lcm
 *
 * @example
 * Input: "(3 + 5) / 2"
 * Output: "4"
 *
 * @example
 * Input: "e ^ 2 + pi"
 * Output: "10.530648752520442"
 *
 * @example
 * Input: "gcd(48, 18) + lcm(4, 5)"
 * Output: "26"
 *
 * @remarks
 * Only displays result if input is a valid math expression.
 * Depends on `mathjs` library. Monitor bundle size when adding/removing features.
 */
export default class Calculator extends Plugin {
  /**
   * MathJS instance with minimal dependencies to reduce bundle size.
   * Only include functions actually used by users.
   *
   * @remarks
   * Bundle impact: Each dependency adds ~1-2KB. Current config ~15KB.
   */
  private static readonly math = create({
    ...absDependencies,
    ...addDependencies,
    ...divideDependencies,
    ...eDependencies,
    ...evaluateDependencies,
    ...expDependencies,
    ...factorialDependencies,
    ...gcdDependencies,
    ...lcmDependencies,
    ...log10Dependencies,
    ...log1pDependencies,
    ...log2Dependencies,
    ...logDependencies,
    ...modDependencies,
    ...multiplyDependencies,
    ...nthRootDependencies,
    ...piDependencies,
    ...powDependencies,
    ...roundDependencies,
    ...signDependencies,
    ...sqrtDependencies,
    ...subtractDependencies
  });

  public constructor() {
    super("calculator");
  }

  /**
   * Attempts to parse and evaluate the search input as a math expression.
   *
   * @returns Formatted result string "expression = result" if valid, undefined otherwise
   */
  protected async run(): Promise<string | undefined> {
    const searchInput = getElement<HTMLInputElement>("q");
    const expression = searchInput.value.trim();

    if (!expression) {
      return undefined;
    }

    return this.evaluateExpression(expression);
  }

  /**
   * Evaluates a mathematical expression safely.
   *
   * @param expression The expression string to evaluate
   * @returns Formatted result or undefined if expression is invalid
   */
  private evaluateExpression(expression: string): string | undefined {
    try {
      const node = Calculator.math.parse(expression);
      const result = node.evaluate();

      return `${node.toString()} = ${result}`;
    } catch (error) {
      // Expression is not valid math - this is expected for non-math queries
      // Silent failure is intentional: only show result if expression is valid
      if (error instanceof Error) {
        console.debug(`Calculator: Invalid expression - ${error.message}`);
      }

      return undefined;
    }
  }

  /**
   * Displays the calculation result to the user.
   *
   * @param result The result string from run()
   */
  protected async post(result: string): Promise<void> {
    appendAnswerElement(result);
  }
}
