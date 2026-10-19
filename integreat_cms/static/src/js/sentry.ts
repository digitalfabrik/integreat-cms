import { browserTracingIntegration, getClient, init } from "@sentry/browser";
/**
 * Initializes Sentry error reporting and performance tracing.
 *
 * The configuration is injected at build time via the webpack DefinePlugin (see `webpack.config.js`).
 * If no DSN is configured, Sentry is not initialized at all and webpack drops it from the bundle.
 */

// https://docs.sentry.io/platforms/javascript/#initialize-the-sentry-sdk
if (!getClient()) {
    const environment = document.documentElement.getAttribute("data-environment");

    if (["production", "staging"].includes(environment)) {
        init({
            dsn: "https://2d8b10e46b9ac2f1bc17477ec97b4099@sentry.tuerantuer.org//9",
            environment,
            release: WEBPACK_VERSION,
            tracesSampleRate: parseFloat(WEBPACK_SENTRY_TRACES_SAMPLE_RATE),
            integrations: [browserTracingIntegration()],
            // Do not send any personally identifiable information
            dataCollection: {
                userInfo: false,
                cookies: false,
                httpHeaders: false,
                httpBodies: [],
                urlQueryParams: false,
            },
        });

        console.debug(`Initializing Sentry error reporting and performance tracing with the following configuration:
- Version: ${WEBPACK_VERSION}
- Traces sample rate: ${WEBPACK_SENTRY_TRACES_SAMPLE_RATE}`);
    } else {
        console.debug(
            `Not initializing Sentry error reporting and performance and tracing (environment = "${environment}")`
        );
    }
}
