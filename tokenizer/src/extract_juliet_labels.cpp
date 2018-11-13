#include <clang-c/Index.h>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <regex>
#include <vector>

void handleTokens(CXTranslationUnit &tu, CXToken *tokens, unsigned count) {
  CXFile file;
  unsigned line, column, offset;
  std::regex label_re("^(/\\*|//)[[:space:]]*([A-Z0-9 ]+):");

  // For each token...
  for (unsigned i = 0; i < count; i++) {
    // If the token is a comment...
    if (clang_getTokenKind(tokens[i]) == CXToken_Comment) {
      // A comment might contain multiple labels.
      // Try to find all of them.
      std::vector<std::string> labels;
      do {
        // If the text looks like a Juliet label (as defined by the 
        // regex at the top of this function), then add it to the 
        // list of labels in this comment block   
        CXString spell = clang_getTokenSpelling(tu, tokens[i]);
        std::string text = clang_getCString(spell);
        clang_disposeString(spell);

        std::smatch matches;
        if (std::regex_search(text, matches, label_re)) {
          labels.push_back(matches[2].str());
        }
        i++;
      } while (i < count && clang_getTokenKind(tokens[i]) == CXToken_Comment);

      // Print out information about the labels we found
      if (labels.size() > 0) {
        CXCursor cursor, parent;
        clang_annotateTokens(tu, &tokens[i], 1, &cursor); 
        parent = clang_getCursorSemanticParent(cursor);

        CXSourceLocation loc = clang_getTokenLocation(tu, tokens[i]);
        clang_getFileLocation(loc, &file, &line, &column, &offset);
        CXString fileName = clang_getFileName(file);
        std::cout << clang_getCString(fileName) << "," << line;
	clang_disposeString(fileName);

        CXCursorKind kind = clang_getCursorKind(parent);
        CXString kindStr = clang_getCursorKindSpelling(kind);
        std::cout << "," << clang_getCString(kindStr);
        clang_disposeString(kindStr);

        CXString spelling = clang_getCursorSpelling(parent);
        std::cout << "," << clang_getCString(spelling);
        clang_disposeString(spelling);
	
        for (const std::string &lbl : labels) {
          std::cout << "," << lbl;
        }
        std::cout << std::endl;
        
      }
    }
  }
}

unsigned getFileSize(const char *fileName) {
  FILE *fp = fopen(fileName, "r");
  fseek(fp, 0, SEEK_END);
  auto size = ftell(fp);
  fclose(fp);
  return size;
}

CXSourceRange getFileRange(const CXTranslationUnit &tu, const char *filename) {
  CXFile file = clang_getFile(tu, filename);
  auto fileSize = getFileSize(filename);

  // Get start and end location of the file, then generate
  // a range from start to end
  CXSourceLocation startLoc = clang_getLocationForOffset(tu, file, 0);
  CXSourceLocation endLoc = clang_getLocationForOffset(tu, file, fileSize);
  return clang_getRange(startLoc, endLoc);
}

int main(int argc, char **argv) {
  // Handle arguments
  if (argc < 2) {
    std::cerr << "Usage: tokenize sourcefile [compiler options ...]\n";
    exit(1);
  }
  // First argument: the path to a source file
  const auto filename = argv[1];

  // Remainder are compiler arguments
  const auto compileArgs = &argv[2];
  // The # of compiler args
  auto numArgs = argc - 2;

  // excludeDeclsFromPCH = 1: precompiled headers omitted in TUs
  // displayDiagnostics = 1: show warnings/errors in TUs
  CXIndex index = clang_createIndex(1, 1);

  // Create a translation unit
  unsigned options = 0;
  options = options | CXTranslationUnit_DetailedPreprocessingRecord;
  CXTranslationUnit tu = clang_parseTranslationUnit(
      index,                // The index to use
      filename,             // The path to the source file
      compileArgs,          // The compiler args
      numArgs,              // Number of compiler args
      nullptr, 0, options); // Remaining options are not needed

  if (tu == nullptr) {
    std::cerr << "Failed to parse translation unit." << std::endl;
    exit(1);
  }

  // Create a CXSouceRange spanning the whole file (start to end)
  CXSourceRange range = getFileRange(tu, filename);
  if (clang_Range_isNull(range)) {
    std::cerr << "Failed to tokenize file." << std::endl;
    exit(1);
  }

  // Tokenize this range (that is, the whole file)
  CXToken *tokens;
  unsigned count;
  clang_tokenize(tu, range, &tokens, &count);

  // Process the tokens
  handleTokens(tu, tokens, count);
  clang_disposeTokens(tu, tokens, count);

  // Clean up
  clang_disposeTranslationUnit(tu);
  clang_disposeIndex(index);
  return 0;
}
