#include <clang/AST/ASTConsumer.h>
#include <clang/AST/DeclTemplate.h>
#include <clang/AST/RecursiveASTVisitor.h>
#include <clang/AST/GlobalDecl.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/FrontendAction.h>
#include <clang/Frontend/FrontendActions.h>
#include <clang/Tooling/Tooling.h>
#include <clang/Tooling/CommonOptionsParser.h>
#include <clang/Basic/TargetInfo.h>
#include <llvm/Support/CommandLine.h>

#include <iostream>
#include <filesystem>
#include <unordered_set>

#include <ogdf/layered/DfsAcyclicSubgraph.h>
#include <ogdf/fileformats/GraphIO.h>
#include <ogdf/uml/UMLGraph.h>
#include <ogdf/uml/UmlModelGraph.h>
#include <ogdf/uml/PlanarizationLayoutUML.h>
#include <ogdf/uml/SubgraphPlanarizerUML.h>
#include <ogdf/fileformats/SvgPrinter.h>

#include <graphviz/gvc.h>

using namespace clang;
using namespace std;

class FindNamedClassVisitor : public clang::RecursiveASTVisitor<FindNamedClassVisitor> {
private:
    bool isInMyPath(clang::FullSourceLoc FullLocation) {
        if (!FullLocation.isValid())
            return false;
        std::string stringPath = Context->getSourceManager().getFilename(FullLocation).str();
        if (!stringPath.empty() && (std::filesystem::canonical(std::filesystem::path(stringPath)).string().rfind(
                "/home/patapouf/projects/CppMonitor", 0) == 0))
            return true;
        return false;
    }

    ogdf::UmlModelGraph ogdfGraph;
    ogdf::UMLGraph ogdfUmlGraph;
    unordered_map<string, ogdf::node> ogdfNodes;

    GVC_t *gvGraphContext;
    Agraph_t *gvGraph;
    unordered_map<string, node_t *> gvNodes;

public:
    explicit FindNamedClassVisitor(clang::ASTContext *Context) :
            Context(Context),
            ogdfUmlGraph(ogdfGraph, ogdf::UMLGraph::nodeLabel | ogdf::UMLGraph::nodeStyle | ogdf::UMLGraph::edgeSubGraphs),
            gvGraphContext(gvContext()), gvGraph(agopen("G", Agdirected, nullptr)) {}

    ~FindNamedClassVisitor() {
        ogdf::SubgraphPlanarizerUML sp;
        ogdf::PlanarizationLayoutUML pl;
        pl.call(ogdfUmlGraph);
        ogdf::GraphIO::write(ogdfUmlGraph, "test.svg", ogdf::GraphIO::drawSVG);

        gvLayout(gvGraphContext, gvGraph, "dot");
        gvRenderFilename(gvGraphContext, gvGraph, "svg", "testGv.svg");
        gvFreeLayout(gvGraphContext, gvGraph);
        agclose(gvGraph);
    }

    bool VisitCXXRecordDecl(CXXRecordDecl *Declaration) {
        if (!isInMyPath(Context->getFullLoc(Declaration->getBeginLoc())))
            return true;
        auto text = Declaration->getQualifiedNameAsString();
        cout << text << endl;

        ogdf::node ogdfn = ogdfGraph.newNode();
        ogdfNodes[text] = ogdfn;
        ogdfUmlGraph.label(ogdfn) = text;
        ogdfUmlGraph.width(ogdfn) = text.size() * 5 + 20;
        ogdfUmlGraph.height(ogdfn) = 20;

        auto gvn = agnode(gvGraph, (char *) text.c_str(), 1);
        gvNodes[text] = gvn;

        //Namespace ns(Declaration->getEnclosingNamespaceContext());
        //for (auto it = Declaration->attr_begin(); it != Declaration->attr_end(); it++)
        //    cout << "  attr : " << (*it)->getNormalizedFullName() << endl;
        //for (auto it = Declaration->decls_begin(); it != Declaration->decls_end(); it++)
        //    cout << "  decl : " << (*it)->getDeclKindName() << endl;
        for (auto it = Declaration->method_begin(); it != Declaration->method_end(); it++)
            cout << "  method : " << (*it)->getQualifiedNameAsString() << endl;
        //for (auto it = Declaration->ctor_begin(); it != Declaration->ctor_end(); it++)
        //    cout << "  ctor : " << (*it)->getQualifiedNameAsString() << endl;
        for (auto it = Declaration->field_begin(); it != Declaration->field_end(); it++)
            cout << "  field : " << (*it)->getQualifiedNameAsString() << endl;
        for (auto it = Declaration->bases_begin(); it != Declaration->bases_end(); it++) {
            cout << "  base : " << it->getTypeSourceInfo()->getType()->getAsCXXRecordDecl()->getQualifiedNameAsString()
                 << endl;

            ogdfGraph.newEdge(ogdfn, ogdfNodes[it->getTypeSourceInfo()->getType()->getAsCXXRecordDecl()->getQualifiedNameAsString()]);

            agedge(gvGraph, gvNodes[it->getTypeSourceInfo()->getType()->getAsCXXRecordDecl()->getQualifiedNameAsString()],
                   gvn, "Ling", 1);
        }
        return true;
    }

private:
    clang::ASTContext *Context;
};

class FindNamedClassConsumer : public clang::ASTConsumer {
public:
    explicit FindNamedClassConsumer(clang::ASTContext *Context) : Visitor(Context) {}

    void HandleTranslationUnit(clang::ASTContext &Context) override {
        Visitor.TraverseDecl(Context.getTranslationUnitDecl());
    }

private:
    FindNamedClassVisitor Visitor;
};

class FindNamedClassAction : public clang::ASTFrontendAction {
public:
    std::unique_ptr<clang::ASTConsumer>
    CreateASTConsumer(clang::CompilerInstance &Compiler, llvm::StringRef InFile) override {
        return std::unique_ptr<clang::ASTConsumer>(new FindNamedClassConsumer(&Compiler.getASTContext()));
    }
};

static llvm::cl::OptionCategory MyToolCategory("CppMonitor", "Decompose your code into UML or graphical diagram");
static llvm::cl::extrahelp CommonHelp(clang::tooling::CommonOptionsParser::HelpMessage);
static llvm::cl::extrahelp MoreHelp("\nMore help text...\n");

int main(int argc, const char **argv) {
    clang::tooling::CommonOptionsParser OptionsParser(argc, argv, MyToolCategory);
    clang::tooling::ClangTool Tool(OptionsParser.getCompilations(), OptionsParser.getSourcePathList());

    return Tool.run(clang::tooling::newFrontendActionFactory<FindNamedClassAction>().get());
}