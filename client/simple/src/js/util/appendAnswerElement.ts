// SPDX-License-Identifier: AGPL-3.0-or-later

import { getElement } from "./getElement.ts";

/**
 * DOM IDs and attributes for answer display elements.
 * Must match corresponding template structure in ./searx/templates/elements/answers.html
 */
const ANSWER_ELEMENTS = {
  CONTAINER_ID: "answers",
  TITLE_ID: "answers-title",
  RESULTS_ID: "results",
  TITLE_CLASS: "title",
  CONTAINER_ROLE: "complementary"
} as const;

/**
 * Appends a new answer element to the search results page.
 *
 * Creates an "Answers" container (if needed) at the top of results and adds the element.
 * Handles both HTMLElement instances and string/number content (converted to DOM).
 *
 * @param content The answer to display (HTMLElement, string, or number)
 *
 * @example
 * ```typescript
 * // With HTMLElement
 * const result = document.createElement('p')
 * result.textContent = 'π ≈ 3.14159'
 * appendAnswerElement(result)
 *
 * // With string
 * appendAnswerElement('2 + 2 = 4')
 * ```
 *
 * @remarks
 * - Container created once and reused for all answers
 * - Answers are displayed prominently before regular search results
 * - String content rendered as plain text (via textContent, not innerHTML)
 */
export function appendAnswerElement(content: HTMLElement | string | number): void {
  const resultsContainer = getElement<HTMLDivElement>(ANSWER_ELEMENTS.RESULTS_ID);
  const answersContainer = getOrCreateAnswersContainer();
  const contentElement = normalizeContent(content);

  answersContainer.appendChild(contentElement);
  resultsContainer.insertAdjacentElement("afterbegin", answersContainer);
}

/**
 * Gets the existing answers container or creates a new one.
 *
 * @returns The answers container DIV element
 */
function getOrCreateAnswersContainer(): HTMLDivElement {
  const existing = getElement<HTMLDivElement>(ANSWER_ELEMENTS.CONTAINER_ID, { assert: false });

  if (existing) {
    return existing;
  }

  return createAnswersContainer();
}

/**
 * Creates the answers container with proper structure and accessibility attributes.
 *
 * @returns A new answers container element
 */
function createAnswersContainer(): HTMLDivElement {
  const title = document.createElement("h4");
  title.className = ANSWER_ELEMENTS.TITLE_CLASS;
  title.id = ANSWER_ELEMENTS.TITLE_ID;
  title.textContent = "Answers: ";

  const container = document.createElement("div");
  container.id = ANSWER_ELEMENTS.CONTAINER_ID;
  container.setAttribute("role", ANSWER_ELEMENTS.CONTAINER_ROLE);
  container.setAttribute("aria-labelledby", ANSWER_ELEMENTS.TITLE_ID);

  container.appendChild(title);

  return container;
}

/**
 * Converts various input types to a DOM element.
 *
 * @param content The content to convert (HTMLElement, string, or number)
 * @returns An HTMLElement ready to be appended to the DOM
 */
function normalizeContent(content: HTMLElement | string | number): HTMLElement {
  if (content instanceof HTMLElement) {
    return content;
  }

  const element = document.createElement("span");
  element.textContent = content.toString();

  return element;
}
