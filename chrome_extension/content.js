/**
 * Universal Content Extraction for Page Q&A
 *
 * Handles various website types:
 * - Wikipedia & wikis
 * - News sites (CNN, BBC, Medium, etc.)
 * - Documentation (MDN, ReadTheDocs, GitBook)
 * - E-commerce (product pages)
 * - Blogs & articles
 * - Generic web pages
 */

const CONFIG = {
    MAX_SECTION_LENGTH: 2500,
    MAX_TOTAL_LENGTH: 60000,
    MIN_PARAGRAPH_LENGTH: 80,
    MIN_SECTION_LENGTH: 50,
};

/**
 * Noise selectors to remove from content
 */
const NOISE_SELECTORS = [
    // Navigation & structure
    'nav', 'aside', 'footer', 'header:not(article header)',
    '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
    '[role="complementary"]', '[role="search"]',

    // Common noise classes/ids
    '.nav', '.navbar', '.navigation', '.menu', '.sidebar', '.side-bar',
    '.footer', '.header', '.masthead', '.breadcrumb', '.breadcrumbs',
    '.advertisement', '.ad', '.ads', '.advert', '.sponsored',
    '.social', '.social-share', '.share-buttons', '.sharing',
    '.comments', '.comment-section', '#comments', '.disqus',
    '.related', '.related-posts', '.recommended', '.suggestions',
    '.newsletter', '.subscribe', '.subscription', '.popup', '.modal',
    '.cookie', '.cookie-banner', '.gdpr', '.consent',
    '.author-bio', '.author-box', '.byline-area',

    // Site-specific
    '#sidebar', '#navigation', '#footer', '#header', '#menu',
    '.wp-sidebar', '.widget-area', '.widgets',

    // Wikipedia specific
    '.toc', '#toc', '.mw-editsection', '.reflist', '.references',
    '.navbox', '.infobox', '.sistersitebox', '.portal',
    '#mw-navigation', '#mw-panel', '.vector-menu', '.vector-dropdown',
    '.mw-indicators', '.catlinks', '#catlinks',

    // Documentation sites
    '.docs-sidebar', '.doc-sidebar', '.toc-wrapper',
    '.page-nav', '.on-this-page',

    // Scripts & hidden
    'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
    '[hidden]', '[aria-hidden="true"]', '.hidden', '.visually-hidden',

    // Forms & inputs
    'form:not([role="search"])', 'input', 'button:not(article button)',
];

/**
 * Main content container selectors (priority order)
 */
const MAIN_CONTENT_SELECTORS = [
    // Article-specific
    'article[role="main"]',
    'main article',
    'article.post',
    'article.entry',
    'article',

    // Role-based
    '[role="main"]',
    'main',

    // Wikipedia
    '#mw-content-text .mw-parser-output',
    '#mw-content-text',
    '#bodyContent',
    '.mw-body-content',

    // Documentation
    '.markdown-body',          // GitHub
    '.documentation-content',
    '.doc-content',
    '.docs-content',
    '.rst-content',            // ReadTheDocs
    '.md-content',             // MkDocs
    '.content-body',

    // News & blogs
    '.post-content',
    '.article-content',
    '.article-body',
    '.entry-content',
    '.story-body',
    '.post-body',
    '.blog-post-content',

    // E-commerce
    '.product-description',
    '.product-details',
    '#product-description',

    // Generic
    '.content',
    '.main-content',
    '.page-content',
    '#content',
    '#main',
    '#main-content',

    // Fallbacks
    '.container main',
    '.wrapper main',
];

/**
 * Find the best main content container
 */
function findMainContent() {
    for (const selector of MAIN_CONTENT_SELECTORS) {
        try {
            const el = document.querySelector(selector);
            if (el) {
                const text = el.innerText?.trim() || '';
                // Must have substantial content
                if (text.length > 300) {
                    return el;
                }
            }
        } catch (e) {
            // Invalid selector, skip
        }
    }

    // Fallback: find the element with most paragraph content
    return findContentByDensity() || document.body;
}

/**
 * Find content area by text density (fallback method)
 */
function findContentByDensity() {
    const candidates = document.querySelectorAll('div, section, article');
    let best = null;
    let bestScore = 0;

    candidates.forEach(el => {
        const paragraphs = el.querySelectorAll('p');
        const text = el.innerText?.trim() || '';

        // Score based on paragraph count and text length
        const score = paragraphs.length * 100 + text.length;

        // Penalize if it's too large (probably a wrapper)
        const isWrapper = el.querySelectorAll('article, main, section').length > 2;
        const adjustedScore = isWrapper ? score * 0.3 : score;

        if (adjustedScore > bestScore && text.length > 500 && text.length < 100000) {
            bestScore = adjustedScore;
            best = el;
        }
    });

    return best;
}

/**
 * Remove noise elements from a cloned container
 */
function removeNoise(container) {
    NOISE_SELECTORS.forEach(selector => {
        try {
            container.querySelectorAll(selector).forEach(el => {
                el.remove();
            });
        } catch (e) {
            // Invalid selector, skip
        }
    });

    // Remove elements with very little text but many links (nav-like)
    container.querySelectorAll('div, ul, section').forEach(el => {
        const links = el.querySelectorAll('a').length;
        const text = el.innerText?.trim() || '';
        const words = text.split(/\s+/).length;

        // High link-to-word ratio suggests navigation
        if (links > 5 && links > words * 0.5 && text.length < 500) {
            el.remove();
        }
    });
}

/**
 * Clean text content
 */
function cleanText(text) {
    if (!text) return '';

    return text
        .replace(/\[edit\]/gi, '')
        .replace(/\[\d+\]/g, '')           // Reference numbers [1], [2]
        .replace(/\s+/g, ' ')               // Multiple spaces
        .replace(/\n\s*\n/g, '\n')          // Multiple newlines
        .trim();
}

/**
 * Extract structured sections from content
 */
function extractSections(container) {
    const sections = [];
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5');

    headings.forEach(heading => {
        const headingText = cleanText(heading.innerText);
        if (!headingText || headingText.length < 3 || headingText.length > 200) return;

        // Collect content until next heading
        let content = headingText + '\n';
        let node = heading.nextElementSibling;

        while (node) {
            if (/^H[1-5]$/.test(node.tagName)) break;

            if (['P', 'UL', 'OL', 'DL', 'TABLE', 'BLOCKQUOTE', 'PRE'].includes(node.tagName)) {
                const text = cleanText(node.innerText);
                if (text && text.length > 20) {
                    content += text + '\n';
                }
            } else if (node.tagName === 'DIV') {
                // Check if div contains direct text or paragraphs
                const divText = cleanText(node.innerText);
                if (divText && divText.length > 30 && divText.length < 3000) {
                    content += divText + '\n';
                }
            }

            if (content.length > CONFIG.MAX_SECTION_LENGTH) break;
            node = node.nextElementSibling;
        }

        if (content.length > CONFIG.MIN_SECTION_LENGTH) {
            sections.push({
                type: 'section',
                text: content.slice(0, CONFIG.MAX_SECTION_LENGTH)
            });
        }
    });

    return sections;
}

/**
 * Extract paragraphs from content
 */
function extractParagraphs(container) {
    const paragraphs = [];
    const seen = new Set();

    container.querySelectorAll('p, li, dd, blockquote, .description, .summary').forEach(el => {
        const text = cleanText(el.innerText);

        // Filter criteria
        if (!text || text.length < CONFIG.MIN_PARAGRAPH_LENGTH) return;
        if (seen.has(text.slice(0, 100))) return;  // Dedup

        seen.add(text.slice(0, 100));
        paragraphs.push({
            type: 'paragraph',
            text: text.slice(0, CONFIG.MAX_SECTION_LENGTH)
        });
    });

    return paragraphs;
}

/**
 * Extract metadata
 */
function extractMetadata() {
    const metadata = [];

    // Title
    const title = document.title?.trim();
    if (title) {
        metadata.push({ type: 'title', text: title });
    }

    // Meta description
    const metaDesc = document.querySelector('meta[name="description"]')?.content?.trim();
    if (metaDesc && metaDesc.length > 30) {
        metadata.push({ type: 'meta', text: metaDesc });
    }

    // Open Graph description (often better)
    const ogDesc = document.querySelector('meta[property="og:description"]')?.content?.trim();
    if (ogDesc && ogDesc.length > 30 && ogDesc !== metaDesc) {
        metadata.push({ type: 'meta', text: ogDesc });
    }

    // Article-specific metadata
    const articleTitle = document.querySelector('h1.title, h1.entry-title, h1.post-title, article h1')?.innerText?.trim();
    if (articleTitle && articleTitle !== title && articleTitle.length > 5) {
        metadata.push({ type: 'heading', text: articleTitle });
    }

    return metadata;
}

/**
 * Extract product information (e-commerce)
 */
function extractProductInfo() {
    const info = [];

    // Product name
    const productName = document.querySelector(
        '.product-title, .product-name, [itemprop="name"], h1.product_title'
    )?.innerText?.trim();

    if (productName) {
        info.push({ type: 'product', text: `Product: ${productName}` });
    }

    // Price
    const price = document.querySelector(
        '.price, .product-price, [itemprop="price"], .offer-price'
    )?.innerText?.trim();

    if (price) {
        info.push({ type: 'product', text: `Price: ${price}` });
    }

    // Description
    const desc = document.querySelector(
        '.product-description, .product-details, [itemprop="description"]'
    )?.innerText?.trim();

    if (desc && desc.length > 50) {
        info.push({ type: 'product', text: cleanText(desc).slice(0, CONFIG.MAX_SECTION_LENGTH) });
    }

    return info;
}

/**
 * Main extraction function
 */
function extractContent() {
    const sections = [];
    let totalLength = 0;

    // 1. Extract metadata
    const metadata = extractMetadata();
    for (const item of metadata) {
        sections.push(item);
        totalLength += item.text.length;
    }

    // 2. Check for product page
    const productInfo = extractProductInfo();
    if (productInfo.length > 0) {
        for (const item of productInfo) {
            if (totalLength < CONFIG.MAX_TOTAL_LENGTH) {
                sections.push(item);
                totalLength += item.text.length;
            }
        }
    }

    // 3. Find and clone main content
    const mainContent = findMainContent();
    const contentClone = mainContent.cloneNode(true);
    removeNoise(contentClone);

    // 4. Try section-based extraction (structured content)
    const structuredSections = extractSections(contentClone);
    for (const section of structuredSections) {
        if (totalLength >= CONFIG.MAX_TOTAL_LENGTH) break;
        if (!sections.some(s => s.text.includes(section.text.slice(0, 100)))) {
            sections.push(section);
            totalLength += section.text.length;
        }
    }

    // 5. Extract paragraphs (fill gaps)
    if (totalLength < CONFIG.MAX_TOTAL_LENGTH * 0.7) {
        const paragraphs = extractParagraphs(contentClone);
        for (const para of paragraphs) {
            if (totalLength >= CONFIG.MAX_TOTAL_LENGTH) break;
            // Avoid duplicates
            if (!sections.some(s => s.text.includes(para.text.slice(0, 80)))) {
                sections.push(para);
                totalLength += para.text.length;
            }
        }
    }

    // 6. Fallback: get clean body text if not enough content
    if (totalLength < 500) {
        const bodyText = cleanText(contentClone.innerText);
        if (bodyText && bodyText.length > 200) {
            sections.push({
                type: 'body',
                text: bodyText.slice(0, CONFIG.MAX_SECTION_LENGTH * 3)
            });
        }
    }

    const result = {
        url: window.location.href,
        sections: sections.filter(s => s.text && s.text.length > 30)
    };

    console.log(`[PageQA] Extracted ${result.sections.length} sections, ${totalLength} chars from ${window.location.hostname}`);

    return result;
}

// Listen for extraction requests
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
    if (req.type === "EXTRACT") {
        try {
            const result = extractContent();
            console.log(`[PageQA] Sending ${result.sections.length} sections`);
            sendResponse(result);
        } catch (error) {
            console.error('[PageQA] Extraction error:', error);
            // Fallback extraction
            sendResponse({
                url: window.location.href,
                sections: [{
                    type: 'body',
                    text: document.body.innerText?.slice(0, 10000) || ''
                }],
                error: error.message
            });
        }
    }
    return true; // Keep message channel open for async response
});
