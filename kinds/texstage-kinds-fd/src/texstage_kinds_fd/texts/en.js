// SPDX-License-Identifier: Apache-2.0
export default {
  "fd-closure:ok": "Set received",
  "fd-closure:invalid": "Check the attribute names and separators",
  setSyntax: () => "Separate attribute names with commas or spaces. Enter {} for the empty set.",
  unknownAttribute: ({name}) => `The relation has no attribute named ${name}. Use the spelling shown in the question.`,
};
