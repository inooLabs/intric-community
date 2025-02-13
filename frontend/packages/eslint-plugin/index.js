import fs from "fs"

import noIgnoredUnsub from "./rules/no-ignored-unsubscriber.js"
import noIgnoredRemoveHandler from "./rules/no-ignored-removehandler.js"

const pkg = JSON.parse(
  fs.readFileSync(new URL("./package.json", import.meta.url), "utf8")
)

/** @type {import("eslint").ESLint.Plugin} */
const plugin = {
  meta: {
    name: pkg.name,
    version: pkg.version,
  },
  configs: {},
  rules: {
    "no-ignored-unsubscriber": noIgnoredUnsub,
    "no-ignored-removehandler": noIgnoredRemoveHandler,
  },
}

Object.assign(plugin.configs, {
  recommended: [
    {
      plugins: {
        intric: plugin,
      },
      rules: {
        "intric/no-ignored-unsubscriber": "error",
        "intric/no-ignored-removehandler": "error",
      },
    },
  ],
})

export default plugin
