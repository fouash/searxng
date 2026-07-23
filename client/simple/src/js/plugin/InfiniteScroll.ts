// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../Plugin.ts";
import { http, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Automatically loads the next page when scrolling to bottom of the current page.
 *
 * Uses Intersection Observer API to detect when user scrolls near the last article,
 * then loads the next page via AJAX and appends results to the current page.
 */
export default class InfiniteScroll extends Plugin {
  private static readonly SCROLL_TRIGGER_MARGIN = "320px";
  private static readonly OBSERVED_SELECTOR = "article.result:last-child";
  private static readonly LAST_ARTICLE_SELECTOR = "#urls article";
  private static readonly HORIZONTAL_DIVIDER = "hr";
  private static readonly IMAGE_ONLY_CLASS = "only_template_images";
  private static readonly ERROR_CLASS = "dialog-error";

  private observer: IntersectionObserver | null = null;

  public constructor() {
    super("infiniteScroll");
  }

  protected async run(): Promise<void> {
    const resultsElement = getElement<HTMLElement>("results");
    const hasOnlyImages = resultsElement.classList.contains(InfiniteScroll.IMAGE_ONLY_CLASS);

    this.observer = this.createIntersectionObserver(hasOnlyImages);
    this.observeInitialElement();
  }

  private createIntersectionObserver(hasOnlyImages: boolean): IntersectionObserver {
    return new IntersectionObserver(
      (entries) => this.handleIntersection(entries, hasOnlyImages),
      { rootMargin: InfiniteScroll.SCROLL_TRIGGER_MARGIN }
    );
  }

  private handleIntersection(entries: IntersectionObserverEntry[], hasOnlyImages: boolean): void {
    const [paginationEntry] = entries;

    if (!paginationEntry?.isIntersecting) {
      return;
    }

    if (!this.observer) {
      return;
    }

    this.observer.unobserve(paginationEntry.target);
    this.loadNextPageAndObserve(hasOnlyImages);
  }

  private observeInitialElement(): void {
    if (!this.observer) {
      return;
    }

    const initialElement = document.querySelector<HTMLElement>(InfiniteScroll.OBSERVED_SELECTOR);
    if (initialElement) {
      this.observer.observe(initialElement);
    }
  }

  private async loadNextPageAndObserve(hasOnlyImages: boolean): Promise<void> {
    try {
      await this.loadNextPage(hasOnlyImages);
      this.observeNextElement();
    } catch (error) {
      this.displayError(error);
    }
  }

  private async loadNextPage(hasOnlyImages: boolean): Promise<void> {
    const spinnerElement = this.createSpinner();
    const paginationElement = this.getPaginationElement();

    paginationElement.replaceChildren(spinnerElement);

    const searchForm = this.getSearchForm();
    const paginationForm = this.getPaginationForm();
    const action = searchForm.getAttribute("action");

    if (!action) {
      throw new Error("Search form action not defined");
    }

    const response = await http("POST", action, { body: new FormData(paginationForm) });
    const nextPageHtml = await response.text();

    if (!nextPageHtml) {
      return;
    }

    this.appendNextPageResults(nextPageHtml, hasOnlyImages);
  }

  private appendNextPageResults(html: string, hasOnlyImages: boolean): void {
    const parser = new DOMParser();
    const nextPageDoc = parser.parseFromString(html, "text/html");

    const nextArticles = Array.from(nextPageDoc.querySelectorAll<HTMLElement>(InfiniteScroll.LAST_ARTICLE_SELECTOR));
    const nextPaginationElement = nextPageDoc.querySelector<HTMLElement>("#pagination");

    const paginationElement = document.querySelector<HTMLElement>("#pagination");
    paginationElement?.remove();

    const urlsElement = this.getUrlsElement();

    if (nextArticles.length > 0 && !hasOnlyImages) {
      urlsElement.appendChild(document.createElement(InfiniteScroll.HORIZONTAL_DIVIDER));
    }

    urlsElement.append(...nextArticles);

    if (nextPaginationElement) {
      const resultsElement = document.querySelector<HTMLElement>("#results");
      resultsElement?.appendChild(nextPaginationElement);
    }
  }

  private observeNextElement(): void {
    if (!this.observer) {
      return;
    }

    const nextElement = document.querySelector<HTMLElement>(InfiniteScroll.OBSERVED_SELECTOR);
    if (nextElement) {
      this.observer.observe(nextElement);
    }
  }

  private displayError(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Failed to load next page:", message);

    const errorElement = document.createElement("div");
    errorElement.className = InfiniteScroll.ERROR_CLASS;
    errorElement.setAttribute("role", "alert");
    errorElement.textContent = settings.translations?.error_loading_next_page ?? "Error loading next page";

    const paginationElement = document.querySelector<HTMLElement>("#pagination");
    paginationElement?.replaceChildren(errorElement);
  }

  private createSpinner(): HTMLElement {
    const spinner = document.createElement("div");
    spinner.className = "loader";
    return spinner;
  }

  private getSearchForm(): HTMLFormElement {
    const form = document.querySelector<HTMLFormElement>("#search");
    assertElement(form);
    return form;
  }

  private getPaginationForm(): HTMLFormElement {
    const form = document.querySelector<HTMLFormElement>("#pagination form.next_page");
    assertElement(form);
    return form;
  }

  private getPaginationElement(): HTMLElement {
    const element = document.querySelector<HTMLElement>("#pagination");
    assertElement(element);
    return element;
  }

  private getUrlsElement(): HTMLElement {
    const element = document.querySelector<HTMLElement>("#urls");
    assertElement(element);
    return element;
  }

  protected async post(): Promise<void> {
    // Cleanup on plugin unload
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
  }
}
