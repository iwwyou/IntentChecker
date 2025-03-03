from collections import defaultdict, deque
from Parser.SolidityParser import SolidityParser
from Parser.SolidityVisitor import SolidityVisitor
from Utils.Interval import IntegerInterval
from Utils.cfg import *
from Utils.util import * # Expression, Variables class
from Analyzer import ContractAnalyzer
import re

class EnhancedSolidityVisitor(SolidityVisitor):

    def __init__(self, contract_analyzer):
        self.contract_analyzer = contract_analyzer

    # Visit a parse tree produced by SolidityParser#sourceUnit.
    def visitSourceUnit(self, ctx:SolidityParser.SourceUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#pragmaDirective.
    def visitPragmaDirective(self, ctx:SolidityParser.PragmaDirectiveContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#pragmaName.
    def visitPragmaName(self, ctx:SolidityParser.PragmaNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#pragmaValue.
    def visitPragmaValue(self, ctx:SolidityParser.PragmaValueContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#version.
    def visitVersion(self, ctx:SolidityParser.VersionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#versionOperator.
    def visitVersionOperator(self, ctx:SolidityParser.VersionOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#versionConstraint.
    def visitVersionConstraint(self, ctx:SolidityParser.VersionConstraintContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#importDeclaration.
    def visitImportDeclaration(self, ctx:SolidityParser.ImportDeclarationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#importDirective.
    def visitImportDirective(self, ctx:SolidityParser.ImportDirectiveContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#importPath.
    def visitImportPath(self, ctx:SolidityParser.ImportPathContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#symbolAliases.
    def visitSymbolAliases(self, ctx:SolidityParser.SymbolAliasesContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#contractDefinition.
    def visitContractDefinition(self, ctx:SolidityParser.ContractDefinitionContext):
        contract_name = ctx.identifier().getText()

        # ContractAnalyzer에서 해당 컨트랙트의 CFG 생성
        self.contract_analyzer.make_contract_cfg(contract_name)
        return

    # Visit a parse tree produced by SolidityParser#interfaceDefinition.
    def visitInterfaceDefinition(self, ctx:SolidityParser.InterfaceDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#libraryDefinition.
    def visitLibraryDefinition(self, ctx:SolidityParser.LibraryDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#inheritanceSpecifier.
    def visitInheritanceSpecifier(self, ctx:SolidityParser.InheritanceSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#callArgumentList.
    def visitCallArgumentList(self, ctx:SolidityParser.CallArgumentListContext):
        argument_list = []

        # 1. 명명되지 않은 인자 리스트 (표현식 목록) 처리
        if ctx.expression():
            for expr in ctx.expression():
                # expression 각각을 방문하여 처리한 결과를 리스트에 추가
                argument_list.append(self.visitExpression(expr))

        # 2. 명명된 인자 처리 (identifier: expression 쌍)
        elif ctx.identifier() and ctx.expression():
            named_arguments = {}
            for identifier, expression in zip(ctx.identifier(), ctx.expression()):
                # identifier와 해당 expression을 각각 방문한 결과로 dictionary에 추가
                named_arguments[identifier.getText()] = self.visitExpression(expression)

            argument_list.append(named_arguments)

        return argument_list


    # Visit a parse tree produced by SolidityParser#identifierPath.
    def visitIdentifierPath(self, ctx:SolidityParser.IdentifierPathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#constantVariableDeclaration.
    def visitConstantVariableDeclaration(self, ctx:SolidityParser.ConstantVariableDeclarationContext):
        var_type = ctx.typeName().getText()
        var_name = ctx.identifier().getText()

        # 타입 분석
        type_context = ctx.typeName()

        # 기본 자료형인 경우
        if isinstance(type_context, SolidityParser.ElementaryTypeNameContext):
            if var_type.startswith('int') or var_type.startswith('uint'):
                if var_type == 'int' or var_type == 'uint':
                    length = 256  # 기본 길이는 256
                else:
                    length = int(var_type[len('int'):])  # 타입의 길이 추출
                variable_obj = Variables(var_name, metaType='elementary', var_type=var_type, intTypeLength=length)
            else:
                variable_obj = Variables(var_name, metaType='elementary', var_type=var_type)

        # Mapping 타입이나 배열 등의 다른 타입 처리 필요 시 추가

        # 초기화 식 처리
        if ctx.expression():
            init_expr = self.visitExpression(ctx.expression())
        else:
            init_expr = None

        # ContractAnalyzer 호출
        self.contract_analyzer.process_constant_variable(variable_obj, init_expr)

        return

    # Visit a parse tree produced by SolidityParser#contractBodyElement.
    def visitContractBodyElement(self, ctx:SolidityParser.ContractBodyElementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#constructorDefinition.
    def visitConstructorDefinition(self, ctx: SolidityParser.ConstructorDefinitionContext):
        constructor_name = "constructor"

        # 파라미터 리스트 처리
        parameters = {}
        if ctx.parameterList():
            parameters = self.visitParameterList(ctx.parameterList())

        # Modifier 처리
        modifiers = []
        if ctx.modifierInvocation():
            for modifier_ctx in ctx.modifierInvocation():
                modifier_name = modifier_ctx.identifierPath().getText()
                modifiers.append(modifier_name)

        # ContractAnalyzer로 전달하여 처리
        self.contract_analyzer.process_constructor_definition(
            constructor_name=constructor_name,
            parameters=parameters,
            modifiers=modifiers
        )

    # Visit a parse tree produced by SolidityParser#fallbackFunctionDefinition.
    def visitFallbackFunctionDefinition(self, ctx:SolidityParser.FallbackFunctionDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#receiveFunctionDefinition.
    def visitReceiveFunctionDefinition(self, ctx:SolidityParser.ReceiveFunctionDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#stateVariableDeclaration.
    def visitStateVariableDeclaration(self, ctx: SolidityParser.StateVariableDeclarationContext):
        var_name = ctx.identifier().getText()

        # 1. 기본 Variables 객체 생성 (초기에는 타입을 모름)
        variable_obj = None

        # 2. 타입 분석
        type_ctx = ctx.typeName()
        type_obj = SolType()
        type_obj = self.visitTypeName(type_ctx, type_obj)  # SolType 객체 반환

        # 3. 변수 객체 생성 (타입에 따라 다름)
        if type_obj.typeCategory == 'array':
            variable_obj = ArrayVariable(identifier=var_name, base_type=type_obj.arrayBaseType,
                                         array_length=type_obj.arrayLength, is_dynamic=type_obj.isDynamicArray,
                                         scope='state')
        elif type_obj.typeCategory == 'struct':
            variable_obj = StructVariable(identifier=var_name, struct_type=type_obj.structTypeName, scope='state')
        elif type_obj.typeCategory == 'mapping':
            variable_obj = MappingVariable(identifier=var_name,
                                           key_type=type_obj.mappingKeyType,
                                           value_type=type_obj.mappingValueType,
                                           scope='state')
        else:
            variable_obj = Variables(identifier=var_name, scope='state')
            variable_obj.typeInfo = type_obj

        # 4. 초기값 처리 (있을 경우)
        if ctx.expression():
            init_expr_ctx = ctx.expression()
            init_expr = self.visitExpression(init_expr_ctx)  # Expression 객체 반환
        else:
            init_expr = None

        # 5. ContractAnalyzer 호출 (processStateVariable)
        self.contract_analyzer.process_state_variable(variable_obj, init_expr)

    # Visit a parse tree produced by SolidityParser#errorDefinition.
    def visitErrorDefinition(self, ctx:SolidityParser.ErrorDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#errorParameter.
    def visitErrorParameter(self, ctx:SolidityParser.ErrorParameterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#usingDirective.
    def visitUsingDirective(self, ctx:SolidityParser.UsingDirectiveContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#userDefinableOperators.
    def visitUserDefinableOperators(self, ctx:SolidityParser.UserDefinableOperatorsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#structDefinition.
    def visitStructDefinition(self, ctx:SolidityParser.StructDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#structMember.
    def visitStructMember(self, ctx: SolidityParser.StructMemberContext):
        # 1. 타입과 변수 이름 가져오기
        var_type = ctx.typeName().getText()
        var_name = ctx.identifier().getText()

        # 2. ContractAnalyzer로 전달하여 처리
        self.contract_analyzer.process_struct_member(var_name, var_type)

    # Visit a parse tree produced by SolidityParser#modifierDefinition.
    def visitModifierDefinition(self, ctx: SolidityParser.ModifierDefinitionContext):
        # 1. Modifier 이름을 가져옴
        modifier_name = ctx.identifier().getText()

        # 2. 파라미터가 존재하는지 확인
        parameters = None
        if ctx.parameterList():
            parameters = self.visitParameterList(ctx.parameterList())

        self.contract_analyzer.process_modifier_definition(modifier_name, parameters)

    # Visit a parse tree produced by SolidityParser#visibility.
    def visitVisibility(self, ctx:SolidityParser.VisibilityContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#modifierInvocation.
    def visitModifierInvocation(self, ctx:SolidityParser.ModifierInvocationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#functionDefinition.
    def visitFunctionDefinition(self, ctx:SolidityParser.FunctionDefinitionContext):
        # 1. Function Name 확인 (identifier만 처리)
        function_name = ctx.identifier().getText() if ctx.identifier() else None
        if not function_name:
            raise ValueError("Function name is missing")

        # 2. 파라미터 처리
        parameters = {}
        if ctx.parameterList():
            parameters = self.visitParameterList(ctx.parameterList(0))

        # 3. Modifier 처리
        modifiers = []
        for spec in ctx.getChildren():
            if isinstance(spec, SolidityParser.ModifierInvocationContext):
                modifier_name = spec.identifierPath().getText()
                modifiers.append(modifier_name)

        # 4. 반환 타입 처리 (returns)
        returns = {}
        if ctx.parameterList(1):  # 두 번째 parameterList가 반환 타입
            returns = self.visitParameterList(ctx.parameterList(1))

        # 5. FunctionDefinition을 처리하여 ContractAnalyzer에 넘김
        self.contract_analyzer.process_function_definition(
            function_name=function_name,
            parameters=parameters,
            modifiers=modifiers,
            returns=returns
        )

    # Visit a parse tree produced by SolidityParser#eventDefinition.
    def visitEventDefinition(self, ctx:SolidityParser.EventDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#enumDefinition.
    def visitEnumDefinition(self, ctx:SolidityParser.EnumDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#parameterList.
    def visitParameterList(self, ctx:SolidityParser.ParameterListContext):
        parameters = []

        # children 중에서 ','로 파라미터를 나누기 위한 리스트 생성
        param_groups = []
        current_param = []

        # 각 children을 순회하면서 ',' (TerminalNodeImpl)를 기준으로 파라미터 그룹을 나눔
        for child in ctx.children:
            if child.getText() == ',':
                # ','를 만나면 하나의 파라미터 그룹을 완성하여 param_groups에 추가
                param_groups.append(current_param)
                current_param = []
            else:
                # ','가 아니면 해당 child를 현재 파라미터 그룹에 추가
                current_param.append(child)

        # 마지막 파라미터 그룹 추가 (리스트가 끝날 때)
        if current_param:
            param_groups.append(current_param)

        # 각 param_group에서 타입과 변수를 추출
        for param_group in param_groups:
            type_obj = SolType()  # SolType 객체 생성
            var_name = None

            # param_group 내에서 각 요소를 확인
            for elem in param_group:
                if isinstance(elem, SolidityParser.TypeNameContext):
                    # 1. 타입 정보 추출
                    type_obj = self.visitTypeName(elem, type_obj)
                elif isinstance(elem, SolidityParser.IdentifierContext):
                    # 2. 변수 이름 추출
                    var_name = elem.getText()

            # var_name이 없으면 객체 생성하지 않고 건너뜀
            if var_name is None:
                continue

            # 타입에 따라 적절한 변수 클래스를 생성
            if type_obj.typeCategory == 'array':
                # 배열 타입인 경우 ArrayVariable 생성
                variable_obj = ArrayVariable(
                    identifier=var_name,
                    base_type=type_obj.arrayBaseType,
                    array_length=type_obj.arrayLength,
                    is_dynamic=type_obj.isDynamicArray,
                    scope="local"
                )
                # 배열 요소 초기화
                variable_obj.initialize_elements(IntegerInterval(0, 0))  # 기본 interval 설정

            elif type_obj.typeCategory == 'struct':
                # 구조체 타입인 경우 StructVariable 생성
                variable_obj = StructVariable(
                    identifier=var_name,
                    struct_type=type_obj.structTypeName,
                    scope="local"
                )

            else:
                # 기본 타입인 경우 Variables 객체 생성
                variable_obj = Variables(identifier=var_name, scope="local")
                variable_obj.typeInfo = type_obj  # SolType 객체를 typeInfo로 설정
                if type_obj.typeCategory == "elementary":
                    if type_obj.elementaryTypeName == "address":
                        variable_obj.value = self.contract_analyzer.fixed_address

            # 리스트에 Variables 객체 추가
            parameters.append(variable_obj)

        return parameters

    # Visit a parse tree produced by SolidityParser#eventParameter.
    def visitEventParameter(self, ctx:SolidityParser.EventParameterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:SolidityParser.VariableDeclarationContext):
        var_type = ctx.typeName().getText()
        var_name = ctx.identifier().getText()

        # 3. 타입 분석
        type_context = ctx.typeName()  # typeName의 첫 번째 child를 가져옴

        # a. elementaryTypeName (기본 자료형)
        if isinstance(type_context, SolidityParser.ElementaryTypeNameContext):
            if var_type.startswith('int') or var_type.startswith('uint'):
                if var_type == 'int' or var_type == 'uint':
                    length = 256  # 기본 길이는 256
                else:
                    length = int(var_type[len('int'):])  # 타입의 길이 추출
                var_type_info = {'type': var_type, 'length': length}
            else:
                var_type_info = {'type': var_type}

        # b. mapping (맵핑 타입) 추후 보완
        elif isinstance(type_context, SolidityParser.MappingContext):
            key_type, value_type = self.visitMapping(type_context)
            var_type_info = {'type': 'mapping', 'key_type': key_type, 'value_type': value_type}

        # c. 배열 타입 추후 보완
        elif isinstance(type_context,
                        SolidityParser.TypeNameContext) and ctx.typeName().getChildCount() > 1 and ctx.typeName().getChild(
            1).getText() == '[':
            element_type = type_context.getText()
            array_size = ctx.typeName().expression().getText() if ctx.typeName().expression() else None
            var_type_info = {'type': 'array', 'element_type': element_type, 'size': array_size}

        else:
            var_type_info = {'type': 'unknown'}

        return var_name, var_type_info

    # Visit a parse tree produced by SolidityParser#variableDeclarationTuple.
    def visitVariableDeclarationTuple(self, ctx:SolidityParser.VariableDeclarationTupleContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#typeName.
    def visitTypeName(self, ctx: SolidityParser.TypeNameContext, type_obj):

        if isinstance(ctx, SolidityParser.BasicTypeContext):  # elementaryTypeName (BasicType)
            return self.visitBasicType(ctx, type_obj)
        elif isinstance(ctx, SolidityParser.FunctionTypeContext):  # functionTypeName (FunctionType)
            return self.visitFunctionType(ctx, type_obj)
        elif isinstance(ctx, SolidityParser.MapTypeContext):  # mapping (MapType)
            return self.visitMapType(ctx, type_obj)
        elif isinstance(ctx, SolidityParser.UserDefinedTypeContext):  # identifierPath (StructType)
            return self.visitUserDefinedType(ctx, type_obj)
        elif isinstance(ctx, SolidityParser.ArrayTypeContext):  # typeName '[' expression? ']' (ArrayType)
            return self.visitArrayType(ctx, type_obj)

    # Visit a parse tree produced by SolidityParser#ArrayType.
    def visitArrayType(self, ctx: SolidityParser.TypeNameContext, type_obj):
        # 배열의 기본 타입 처리
        base_type_ctx = ctx.typeName()
        base_type_obj = SolType()
        base_type_obj = self.visitTypeName(base_type_ctx, base_type_obj)

        # 배열 크기 확인
        if ctx.expression():
            array_size_expr = ctx.expression()
            array_size = self.evaluate_expression(array_size_expr)  # 배열 크기를 평가 (정수 값이어야 함)
            is_dynamic = False
        else:
            array_size = 0
            is_dynamic = True

        type_obj.typeCategory = "array"
        type_obj.arrayBaseType = base_type_obj  # 재귀적으로 타입 표현
        type_obj.arrayLength = array_size
        type_obj.isDynamicArray = is_dynamic

        return type_obj

    # Visit a parse tree produced by SolidityParser#BasicType.
    def visitBasicType(self, ctx: SolidityParser.ElementaryTypeNameContext, type_obj):
        var_type = ctx.getText()
        type_obj.typeCategory = "elementary"
        type_obj.elementaryTypeName = var_type

        if var_type.startswith('int'):
            if var_type == 'int':
                type_obj.intTypeLength = 256  # 기본 길이는 256
            else:
                # 'int' 뒤에 붙은 숫자를 추출하여 비트 길이 설정
                try:
                    type_obj.intTypeLength = int(var_type[3:])  # 'int' 뒤의 숫자를 추출
                except ValueError:
                    raise ValueError(f"Invalid integer type length in '{var_type}'")

        elif var_type.startswith('uint'):
            if var_type == 'uint':
                type_obj.intTypeLength = 256  # 기본 길이는 256
            else:
                # 'uint' 뒤에 붙은 숫자를 추출하여 비트 길이 설정
                try:
                    type_obj.intTypeLength = int(var_type[4:])  # 'uint' 뒤의 숫자를 추출
                except ValueError:
                    raise ValueError(f"Invalid unsigned integer type length in '{var_type}'")

        return type_obj

    # Visit a parse tree produced by SolidityParser#FunctionType.
    def visitFunctionType(self, ctx: SolidityParser.FunctionTypeNameContext, type_obj):
        # 함수 타입 처리 (필요한 경우)
        type_obj.typeCategory = "function"
        # 추가적인 정보 처리 필요 시 여기서 처리
        return type_obj

    # Visit a parse tree produced by SolidityParser#StructType.
    def visitUserDefinedType(self, ctx: SolidityParser.UserDefinedTypeContext, type_obj):
        """
            사용자 정의 타입(Struct, Enum 등)을 처리합니다.
            :param ctx: IdentifierPathContext
            :param type_obj: SolType 객체
            :return: 수정된 type_obj
            """
        # 타입 이름 추출
        type_name = ctx.getText()

        # 현재 타겟 컨트랙트 이름 가져오기
        contract_name = self.contract_analyzer.current_target_contract

        # 현재 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_analyzer.contract_cfgs.get(contract_name)
        if not contract_cfg:
            raise ValueError(f"Contract '{contract_name}' not found in contract configurations.")

        # 타입이 enum인지 struct인지 확인
        if type_name in contract_cfg.enums:
            # Enum 타입인 경우
            type_obj.typeCategory = "enum"
            type_obj.enumTypeName = type_name
        elif type_name in contract_cfg.structs:
            # Struct 타입인 경우
            type_obj.typeCategory = "struct"
            type_obj.structTypeName = type_name
        else:
            # 정의되지 않은 타입인 경우 예외 처리 또는 기본값 설정
            raise ValueError(f"Type '{type_name}' is not defined as struct or enum in contract '{contract_name}'.")

        return type_obj

    # Visit a parse tree produced by SolidityParser#MapType.
    def visitMapType(self, ctx: SolidityParser.MappingContext, type_obj):
        return self.visitMapping(ctx.mapping(), type_obj)

    # Visit a parse tree produced by SolidityParser#mapping.
    def visitMapping(self, ctx: SolidityParser.MappingContext, type_obj):
        # 키 타입 처리
        key_type_ctx = ctx.mappingKeyType()
        key_type_obj = self.visitMappingKeyType(key_type_ctx)

        # 값 타입 처리
        value_type_ctx = ctx.typeName()
        value_type_obj = SolType()
        value_type_obj = self.visitTypeName(value_type_ctx, value_type_obj)

        type_obj.typeCategory = "mapping"
        type_obj.mappingKeyType = key_type_obj
        type_obj.mappingValueType = value_type_obj

        return type_obj

    # Visit a parse tree produced by SolidityParser#mappingKeyType.
    def visitMappingKeyType(self, ctx:SolidityParser.MappingKeyTypeContext):
        # 키 타입은 elementaryTypeName만 가능
        if ctx.elementaryTypeName() is not None:
            key_type_obj = SolType()
            self.visitBasicType(ctx.elementaryTypeName(), key_type_obj)
            return key_type_obj
        else:
            # Solidity에서 키 타입은 elementary 타입만 허용하므로, 기타 타입은 오류 처리
            raise ValueError("Invalid key type in mapping: {}".format(ctx.getText()))

    # Visit a parse tree produced by SolidityParser#functionTypeName.
    def visitFunctionTypeName(self, ctx:SolidityParser.FunctionTypeNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveSourceUnit.
    def visitInteractiveSourceUnit(self, ctx:SolidityParser.InteractiveSourceUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveEnumUnit.
    def visitInteractiveEnumUnit(self, ctx:SolidityParser.InteractiveEnumUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveStructUnit.
    def visitInteractiveStructUnit(self, ctx:SolidityParser.InteractiveStructUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveBlockUnit.
    def visitInteractiveBlockUnit(self, ctx:SolidityParser.InteractiveBlockUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveDoWhileUnit.
    def visitInteractiveDoWhileUnit(self, ctx:SolidityParser.InteractiveDoWhileUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveIfElseUnit.
    def visitInteractiveIfElseUnit(self, ctx:SolidityParser.InteractiveIfElseUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveCatchClauseUnit.
    def visitInteractiveCatchClauseUnit(self, ctx:SolidityParser.InteractiveCatchClauseUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#intentUnit.
    def visitIntentUnit(self, ctx:SolidityParser.IntentUnitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#preExecutionGlobal.
    def visitPreExecutionGlobal(self, ctx:SolidityParser.PreExecutionGlobalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockbaseFee.
    def visitBlockbaseFee(self, ctx:SolidityParser.BlockbaseFeeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockBlobbasefee.
    def visitBlockBlobbasefee(self, ctx:SolidityParser.BlockBlobbasefeeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockChainid.
    def visitBlockChainid(self, ctx:SolidityParser.BlockChainidContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockDifficulty.
    def visitBlockDifficulty(self, ctx:SolidityParser.BlockDifficultyContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockGaslimit.
    def visitBlockGaslimit(self, ctx:SolidityParser.BlockGaslimitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockNumber.
    def visitBlockNumber(self, ctx:SolidityParser.BlockNumberContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockPrevrandao.
    def visitBlockPrevrandao(self, ctx:SolidityParser.BlockPrevrandaoContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#BlockTimestamp.
    def visitBlockTimestamp(self, ctx:SolidityParser.BlockTimestampContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#TxGasprice.
    def visitTxGasprice(self, ctx:SolidityParser.TxGaspriceContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#preExecutionState.
    def visitPreExecutionState(self, ctx:SolidityParser.PreExecutionStateContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#preExecutionLocal.
    def visitPreExecutionLocal(self, ctx:SolidityParser.PreExecutionLocalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#testingExpression.
    def visitTestingExpression(self, ctx:SolidityParser.TestingExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#TestingMemberAccess.
    def visitTestingMemberAccess(self, ctx:SolidityParser.TestingMemberAccessContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#TestingIndexAccess.
    def visitTestingIndexAccess(self, ctx:SolidityParser.TestingIndexAccessContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#numberBoolLiteral.
    def visitNumberBoolLiteral(self, ctx:SolidityParser.NumberBoolLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#postExecutionState.
    def visitPostExecutionState(self, ctx:SolidityParser.PostExecutionStateContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#postExecutionReturn.
    def visitPostExecutionReturn(self, ctx:SolidityParser.PostExecutionReturnContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecution.
    def visitDuringExecution(self, ctx:SolidityParser.DuringExecutionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecutionComment.
    def visitDuringExecutionComment(self, ctx:SolidityParser.DuringExecutionCommentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecutionBeforeAfter.
    def visitDuringExecutionBeforeAfter(self, ctx:SolidityParser.DuringExecutionBeforeAfterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#beforeAfter.
    def visitBeforeAfter(self, ctx:SolidityParser.BeforeAfterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecutionAssignCurrent.
    def visitDuringExecutionAssignCurrent(self, ctx:SolidityParser.DuringExecutionAssignCurrentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#assignCurrent.
    def visitAssignCurrent(self, ctx:SolidityParser.AssignCurrentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecutionReturn.
    def visitDuringExecutionReturn(self, ctx:SolidityParser.DuringExecutionReturnContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#ExpressionReturn.
    def visitExpressionReturn(self, ctx:SolidityParser.ExpressionReturnContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#VarReturn.
    def visitVarReturn(self, ctx:SolidityParser.VarReturnContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#returnVar.
    def visitReturnVar(self, ctx:SolidityParser.ReturnVarContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#duringExecutionGeneral.
    def visitDuringExecutionGeneral(self, ctx:SolidityParser.DuringExecutionGeneralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#comparisonExpression.
    def visitComparisonExpression(self, ctx:SolidityParser.ComparisonExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#logicalOperator.
    def visitLogicalOperator(self, ctx:SolidityParser.LogicalOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#comparisonOperator.
    def visitComparisonOperator(self, ctx:SolidityParser.ComparisonOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#arithmeticExpression.
    def visitArithmeticExpression(self, ctx:SolidityParser.ArithmeticExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#multiplicativeExpression.
    def visitMultiplicativeExpression(self, ctx:SolidityParser.MultiplicativeExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#primaryExpression.
    def visitPrimaryExpression(self, ctx:SolidityParser.PrimaryExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#accessExpression.
    def visitAccessExpression(self, ctx:SolidityParser.AccessExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#additiveOperator.
    def visitAdditiveOperator(self, ctx:SolidityParser.AdditiveOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#multiplicativeOperator.
    def visitMultiplicativeOperator(self, ctx:SolidityParser.MultiplicativeOperatorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveSimpleStatement.
    def visitInteractiveSimpleStatement(self, ctx:SolidityParser.InteractiveSimpleStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveVariableDeclarationStatement.
    def visitInteractiveVariableDeclarationStatement(self, ctx:SolidityParser.InteractiveVariableDeclarationStatementContext):
        # 1. 변수 선언 정보 가져오기
        type_ctx = ctx.variableDeclaration().typeName()
        var_name = ctx.variableDeclaration().identifier().getText()

        # 2. 초기화 값이 있는 경우 처리
        init_expr = None
        if ctx.expression():
            init_expr = self.visitExpression(ctx.expression())

        # 3. 변수 타입 정보 분석 및 적절한 Variables 객체 생성
        type_obj = SolType()
        type_obj = self.visitTypeName(type_ctx, type_obj)  # 타입 정보 분석

        if type_obj.typeCategory == 'array':
            # 배열 타입인 경우 ArrayVariable 생성
            base_type = type_obj.arrayBaseType
            array_length = type_obj.arrayLength
            is_dynamic = type_obj.isDynamicArray
            variable_obj = ArrayVariable(identifier=var_name, base_type=base_type,
                                         array_length=array_length, is_dynamic=is_dynamic, scope='local')
            if not is_dynamic:
                # 정적 배열의 경우 초기화
                variable_obj.initialize_elements(IntegerInterval(0, 0))

        elif type_obj.typeCategory == 'struct':
            # 구조체 타입인 경우 StructVariable 생성
            struct_type = type_obj.structTypeName
            variable_obj = StructVariable(identifier=var_name, struct_type=struct_type, scope='local')

        else:
            # 기본 타입인 경우 Variables 객체 생성
            variable_obj = Variables(identifier=var_name, scope="local")
            variable_obj.typeInfo = type_obj  # SolType 객체를 typeInfo로 설정

        # 5. ContractAnalyzer로 Variables 객체 및 lineComment 전달
        self.contract_analyzer.process_variable_declaration(variable_obj, init_expr)

        return

    # Visit a parse tree produced by SolidityParser#interactiveExpressionStatement.
    def visitInteractiveExpressionStatement(self, ctx:SolidityParser.InteractiveExpressionStatementContext):
        # 1. 표현식 방문
        expr_ctx = ctx.expression()
        expr = self.visitExpression(expr_ctx)

        # Handle assignment expressions
        if isinstance(expr_ctx, SolidityParser.AssignmentContext):
            # Right-hand side expression
            rhs_expr_ctx = expr_ctx.expression(1)

            # Check for specific expression types on the right-hand side
            if isinstance(rhs_expr_ctx, SolidityParser.FunctionCallContext):
                self.contract_analyzer.process_assignment_function_call(expr)
            elif isinstance(rhs_expr_ctx, SolidityParser.FunctionCallOptionsContext):
                self.contract_analyzer.process_assignment_function_call_options(expr)
            elif isinstance(rhs_expr_ctx, SolidityParser.PayableFunctionCallContext):
                self.contract_analyzer.process_assignment_payable_function_call(expr)
            elif isinstance(rhs_expr_ctx, SolidityParser.ConditionalExpContext):
                self.contract_analyzer.process_assignment_conditional_expression(expr)
            else:
                # Regular assignment
                self.contract_analyzer.process_assignment_expression(expr)
        elif isinstance(expr_ctx, SolidityParser.UnaryPrefixOpContext):
            self.contract_analyzer.process_unary_prefix_operation(expr)
        elif isinstance(expr_ctx, SolidityParser.UnarySuffixOpContext):
            self.contract_analyzer.process_unary_suffix_operation(expr)
        elif isinstance(expr_ctx, SolidityParser.FunctionCallContext):
            self.contract_analyzer.process_function_call(expr)
        elif isinstance(expr_ctx, SolidityParser.PayableFunctionCallContext):
            self.contract_analyzer.process_payable_function_call(expr)
        elif isinstance(expr_ctx, SolidityParser.FunctionCallOptionsContext):
            self.contract_analyzer.process_function_call_options(expr)
        else:
            raise ValueError(f"Unsupported expression context in interactiveExpressionStatement: {ctx}")

        return

    # Visit a parse tree produced by SolidityParser#interactiveStateVariableElement.
    def visitInteractiveStateVariableElement(self, ctx:SolidityParser.InteractiveStateVariableElementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveEnumDefinition.
    def visitInteractiveEnumDefinition(self, ctx:SolidityParser.InteractiveEnumDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveStructDefinition.
    def visitInteractiveStructDefinition(self, ctx:SolidityParser.InteractiveStructDefinitionContext):
        struct_name = ctx.identifier().getText()
        self.contract_analyzer.process_struct_definition(struct_name)
        return

    # Visit a parse tree produced by SolidityParser#interactiveEnumItems.
    def visitInteractiveEnumItems(self, ctx:SolidityParser.InteractiveEnumItemsContext):
        enum_items = [identifier.getText() for identifier in ctx.identifier()]

        self.contract_analyzer.process_enum_item(enum_items)

        return

    # Visit a parse tree produced by SolidityParser#interactiveFunctionElement.
    def visitInteractiveFunctionElement(self, ctx:SolidityParser.InteractiveFunctionElementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveBlockItem.
    def visitInteractiveBlockItem(self, ctx:SolidityParser.InteractiveBlockItemContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#dataLocation.
    def visitDataLocation(self, ctx:SolidityParser.DataLocationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#stateMutability.
    def visitStateMutability(self, ctx:SolidityParser.StateMutabilityContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#block.
    def visitBlock(self, ctx:SolidityParser.BlockContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#uncheckedBlock.
    def visitUncheckedBlock(self, ctx:SolidityParser.UncheckedBlockContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#statement.
    def visitStatement(self, ctx:SolidityParser.StatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#expressionStatement.
    def visitExpressionStatement(self, ctx:SolidityParser.ExpressionStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#ifStatement.
    def visitIfStatement(self, ctx:SolidityParser.IfStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#tryStatement.
    def visitTryStatement(self, ctx:SolidityParser.TryStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#catchClause.
    def visitCatchClause(self, ctx:SolidityParser.CatchClauseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#whileStatement.
    def visitWhileStatement(self, ctx:SolidityParser.WhileStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#simpleStatement.
    def visitSimpleStatement(self, ctx:SolidityParser.SimpleStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#forStatement.
    def visitForStatement(self, ctx:SolidityParser.ForStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#inlineArrayExpression.
    def visitInlineArrayExpression(self, ctx:SolidityParser.InlineArrayExpressionContext):
        elements = []

        # 배열의 각 요소들을 순회하며 Expression으로 방문
        for expr_ctx in ctx.expression():
            element_expr = self.visitExpression(expr_ctx)  # 각 요소에 대해 Expression 객체 생성
            elements.append(element_expr)  # 리스트에 추가

        # Expression 객체로 배열을 표현
        array_expr = Expression(
            elements=elements,  # 배열의 요소들 저장
            expr_type='array',  # 표현식 타입을 배열로 지정
            context='InlineArrayExpressionContext'
        )

        return array_expr

    # Visit a parse tree produced by SolidityParser#assemblyStatement.
    def visitAssemblyStatement(self, ctx:SolidityParser.AssemblyStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#assemblyFlags.
    def visitAssemblyFlags(self, ctx:SolidityParser.AssemblyFlagsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#assemblyFlagString.
    def visitAssemblyFlagString(self, ctx:SolidityParser.AssemblyFlagStringContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulStatement.
    def visitYulStatement(self, ctx:SolidityParser.YulStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulBlock.
    def visitYulBlock(self, ctx:SolidityParser.YulBlockContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulVariableDeclaration.
    def visitYulVariableDeclaration(self, ctx:SolidityParser.YulVariableDeclarationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulAssignment.
    def visitYulAssignment(self, ctx:SolidityParser.YulAssignmentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulIfStatement.
    def visitYulIfStatement(self, ctx:SolidityParser.YulIfStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulForStatement.
    def visitYulForStatement(self, ctx:SolidityParser.YulForStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulSwitchStatement.
    def visitYulSwitchStatement(self, ctx:SolidityParser.YulSwitchStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulFunctionDefinition.
    def visitYulFunctionDefinition(self, ctx:SolidityParser.YulFunctionDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulPath.
    def visitYulPath(self, ctx:SolidityParser.YulPathContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulFunctionCall.
    def visitYulFunctionCall(self, ctx:SolidityParser.YulFunctionCallContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulBoolean.
    def visitYulBoolean(self, ctx:SolidityParser.YulBooleanContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulLiteral.
    def visitYulLiteral(self, ctx:SolidityParser.YulLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#yulExpression.
    def visitYulExpression(self, ctx:SolidityParser.YulExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:SolidityParser.DoWhileStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#continueStatement.
    def visitContinueStatement(self, ctx:SolidityParser.ContinueStatementContext):
        return self.contract_analyzer.process_continue_statement()

    # Visit a parse tree produced by SolidityParser#breakStatement.
    def visitBreakStatement(self, ctx:SolidityParser.BreakStatementContext):
        return self.contract_analyzer.process_break_statement()

    # Visit a parse tree produced by SolidityParser#returnStatement.
    def visitReturnStatement(self, ctx:SolidityParser.ReturnStatementContext):
        # 1. 반환되는 expression 처리
        if ctx.expression():
            return_expr = self.visitExpression(ctx.expression())
        else:
            return_expr = None

        # 2. ContractAnalyzer에 반환 표현식 전달
        self.contract_analyzer.process_return_statement(return_expr)

        return

    # Visit a parse tree produced by SolidityParser#emitStatement.
    def visitEmitStatement(self, ctx:SolidityParser.EmitStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#revertStatement.
    def visitRevertStatement(self, ctx:SolidityParser.RevertStatementContext):
        # 1. identifier와 stringLiteral 둘 중 하나를 처리
        revert_identifier = None
        string_literal = None

        if ctx.identifier():
            revert_identifier = self.visitIdentifier(ctx.identifier())
        elif ctx.stringLiteral():
            string_literal = self.visitStringLiteral(ctx.stringLiteral())

        # 2. callArgumentList가 존재하는지 여부 확인 및 처리
        call_argument_list = []
        if ctx.callArgumentList():
            call_argument_list = self.visitCallArgumentList(ctx.callArgumentList())

        # 3. ContractAnalyzer의 process_revert_statement 메소드 호출
        self.contract_analyzer.process_revert_statement(revert_identifier, string_literal, call_argument_list)
        return

    # Visit a parse tree produced by SolidityParser#requireStatement.
    def visitRequireStatement(self, ctx:SolidityParser.RequireStatementContext):
        # 1. 'require'의 조건식(expression)을 방문하여 추출
        condition_expr = self.visit(ctx.expression())

        # 2. 에러 메시지(stringLiteral) 처리 - 선택적
        if ctx.stringLiteral():
            error_message = ctx.stringLiteral().getText()
        else:
            error_message = None

        # 3. ContractAnalyzer에서 process_require_statement 호출
        self.contract_analyzer.process_require_statement(condition_expr, error_message)

        return

    # Visit a parse tree produced by SolidityParser#assertStatement.
    def visitAssertStatement(self, ctx:SolidityParser.AssertStatementContext):
        # 1. expression을 방문해서 조건식을 가져옴
        condition_expr = self.visitExpression(ctx.expression())

        # 2. ContractAnalyzer에서 process_assert_statement 호출
        self.contract_analyzer.process_assert_statement(condition_expr)

    # Visit a parse tree produced by SolidityParser#variableDeclarationStatement.
    def visitVariableDeclarationStatement(self, ctx:SolidityParser.VariableDeclarationStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveStatement.
    def visitInteractiveStatement(self, ctx:SolidityParser.InteractiveStatementContext):
        if ctx.interactiveSimpleStatement():
            return self.visitInteractiveSimpleStatement(ctx.interactiveSimpleStatement())
        elif ctx.interactiveIfStatement():
            return self.visitInteractiveIfStatement(ctx.interactiveIfStatement())
        elif ctx.interactiveForStatement():
            return self.visitInteractiveForStatement(ctx.interactiveForStatement())
        elif ctx.interactiveWhileStatement():
            return self.visitInteractiveWhileStatement(ctx.interactiveWhileStatement())
        elif ctx.interactiveDoWhileDoStatement():
            return self.visitInteractiveDoWhileDoStatement(ctx.interactiveDoWhileDoStatement())
        elif ctx.continueStatement():
            return self.visitContinueStatement(ctx.continueStatement())
        elif ctx.breakStatement():
            return self.visitBreakStatement(ctx.breakStatement())
        elif ctx.interactiveTryStatement():
            return self.visitInteractiveTryStatement(ctx.interactiveTryStatement())
        elif ctx.returnStatement():
            return self.visitReturnStatement(ctx.returnStatement())
        elif ctx.emitStatement():
            return self.visitEmitStatement(ctx.emitStatement())
        elif ctx.revertStatement():
            return self.visitRevertStatement(ctx.revertStatement())
        elif ctx.assemblyStatement():
            # assembly에 대한 처리 (나중에 구현 예정)
            pass
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveIfStatement.
    def visitInteractiveIfStatement(self, ctx:SolidityParser.InteractiveIfStatementContext):
        # 1. 조건식 표현식 방문
        condition_expr = self.visitExpression(ctx.expression())

        # 부모 컨텍스트가 else문에서 온 경우인지 확인
        if ctx.parentCtx and isinstance(ctx.parentCtx, SolidityParser.InteractiveElseStatementContext):
            # else if 문 처리
            self.contract_analyzer.process_else_if_statement(condition_expr)
        else:
            # if 문 처리
            self.contract_analyzer.process_if_statement(condition_expr)

    # Visit a parse tree produced by SolidityParser#interactiveElseStatement.
    def visitInteractiveElseStatement(self, ctx:SolidityParser.InteractiveElseStatementContext):
        # 'else if' 블록인지 아니면 'else' 블록인지를 판단
        if ctx.interactiveIfStatement():
            # 'else if' 문이 존재하는 경우
            return self.visitInteractiveIfStatement(ctx.interactiveIfStatement())
        else:
            # 'else' 블록을 처리
            self.contract_analyzer.process_else_statement()

    # Visit a parse tree produced by SolidityParser#interactiveForStatement.
    def visitInteractiveForStatement(self, ctx:SolidityParser.InteractiveForStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveWhileStatement.
    def visitInteractiveWhileStatement(self, ctx:SolidityParser.InteractiveWhileStatementContext):
        # 1. 조건식 표현식 방문
        condition_expr = self.visitExpression(ctx.expression())

        # 2. ContractAnalyzer의 process_while_statement 호출
        self.contract_analyzer.process_while_statement(condition_expr)

    # Visit a parse tree produced by SolidityParser#interactiveDoWhileDoStatement.
    def visitInteractiveDoWhileDoStatement(self, ctx:SolidityParser.InteractiveDoWhileDoStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveDoWhileWhileStatement.
    def visitInteractiveDoWhileWhileStatement(self, ctx:SolidityParser.InteractiveDoWhileWhileStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveTryStatement.
    def visitInteractiveTryStatement(self, ctx:SolidityParser.InteractiveTryStatementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#interactiveCatchClause.
    def visitInteractiveCatchClause(self, ctx:SolidityParser.InteractiveCatchClauseContext):
        catch_node = f"Catch_{ctx.start.line}"
        self.contract_analyzer.add_control_flow_node(catch_node, ctx)

        # Catch 블록 내의 매개변수 목록 처리
        if ctx.parameterList():
            self.visit(ctx.parameterList())

        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#elementaryTypeName.
    def visitElementaryTypeName(self, ctx:SolidityParser.ElementaryTypeNameContext):
        return self.visitChildren(ctx)

    def visitExpression(self, ctx):
        # IndexAccess (배열 인덱스 접근)
        if isinstance(ctx, SolidityParser.IndexAccessContext):
            return self.visitIndexAccess(ctx)

        # IndexRangeAccess (배열 범위 접근)
        elif isinstance(ctx, SolidityParser.IndexRangeAccessContext):
            return self.visitIndexRangeAccess(ctx)

        # MemberAccess (객체 멤버 접근)
        elif isinstance(ctx, SolidityParser.MemberAccessContext):
            return self.visitMemberAccess(ctx)

        # FunctionCallOptions (함수 호출 옵션)
        elif isinstance(ctx, SolidityParser.FunctionCallOptionsContext):
            return self.visitFunctionCallOptions(ctx)

        # FunctionCall (함수 호출)
        elif isinstance(ctx, SolidityParser.FunctionCallContext):
            return self.visitFunctionCall(ctx)

        # PayableFunctionCall (Payable 함수 호출)
        elif isinstance(ctx, SolidityParser.PayableFunctionCallContext):
            return self.visitPayableFunctionCall(ctx)

        # TypeConversion (타입 변환)
        elif isinstance(ctx, SolidityParser.TypeConversionContext):
            return self.visitTypeConversion(ctx)

        # UnaryPrefixOp (단항 연산자 - 전위)
        elif isinstance(ctx, SolidityParser.UnaryPrefixOpContext):
            return self.visitUnaryPrefixOp(ctx)

        # UnarySuffixOp (단항 연산자 - 후위)
        elif isinstance(ctx, SolidityParser.UnarySuffixOpContext):
            return self.visitUnarySuffixOp(ctx)

        # Exponentiation (지수 연산)
        elif isinstance(ctx, SolidityParser.ExponentiationContext):
            return self.visitExponentiation(ctx)

        # MultiplicativeOp (곱셈/나눗셈/나머지 연산)
        elif isinstance(ctx, SolidityParser.MultiplicativeOpContext):
            return self.visitMultiplicativeOp(ctx)

        # AdditiveOp (덧셈/뺄셈 연산)
        elif isinstance(ctx, SolidityParser.AdditiveOpContext):
            return self.visitAdditiveOp(ctx)

        # ShiftOp (비트 시프트 연산)
        elif isinstance(ctx, SolidityParser.ShiftOpContext):
            return self.visitShiftOp(ctx)

        # BitAndOp (비트 AND 연산)
        elif isinstance(ctx, SolidityParser.BitAndOpContext):
            return self.visitBitAndOp(ctx)

        # BitXorOp (비트 XOR 연산)
        elif isinstance(ctx, SolidityParser.BitXorOpContext):
            return self.visitBitXorOp(ctx)

        # BitOrOp (비트 OR 연산)
        elif isinstance(ctx, SolidityParser.BitOrOpContext):
            return self.visitBitOrOp(ctx)

        # RelationalOp (관계 연산자)
        elif isinstance(ctx, SolidityParser.RelationalOpContext):
            return self.visitRelationalOp(ctx)

        # EqualityOp (동등성 연산자)
        elif isinstance(ctx, SolidityParser.EqualityOpContext):
            return self.visitEqualityOp(ctx)

        # AndOperation (논리 AND 연산자)
        elif isinstance(ctx, SolidityParser.AndOperationContext):
            return self.visitAndOperation(ctx)

        # OrOperation (논리 OR 연산자)
        elif isinstance(ctx, SolidityParser.OrOperationContext):
            return self.visitOrOperation(ctx)

        # ConditionalExp (삼항 연산자)
        elif isinstance(ctx, SolidityParser.ConditionalExpContext):
            return self.visitConditionalExp(ctx)

        # Assignment (할당 연산자)
        elif isinstance(ctx, SolidityParser.AssignmentContext):
            return self.visitAssignment(ctx)

        # NewExp (new 연산자)
        elif isinstance(ctx, SolidityParser.NewExpContext):
            return self.visitNewExp(ctx)

        # TupleExp (튜플)
        elif isinstance(ctx, SolidityParser.TupleExpContext):
            return self.visitTupleExp(ctx)

        # InlineArrayExp (배열 리터럴)
        elif isinstance(ctx, SolidityParser.InlineArrayExpContext):
            return self.visitInlineArrayExp(ctx)

        # IdentifierExp (식별자)
        elif isinstance(ctx, SolidityParser.IdentifierExpContext):
            return self.visitIdentifierExp(ctx)

        # LiteralExp (리터럴)
        elif isinstance(ctx, SolidityParser.LiteralExpContext):
            return self.visitLiteralExp(ctx)

        # LiteralSubDenomination (리터럴 서브 단위)
        elif isinstance(ctx, SolidityParser.LiteralSubDenominationContext):
            return self.visitLiteralSubDenomination(ctx)

        # TypeNameExp (타입 이름)
        elif isinstance(ctx, SolidityParser.TypeNameExpContext):
            return self.visitTypeNameExp(ctx)

        else:
            raise NotImplementedError(f"Unhandled expression context: {type(ctx).__name__}")

    def visitIndexAccess(self, ctx):
        # 1. 배열 또는 매핑 표현식 방문
        base_expr = self.visitExpression(ctx.expression(0))

        # 2. 인덱스 표현식 방문 (optional)
        if ctx.expression(1):
            index_expr = self.visitExpression(ctx.expression(1))
        else:
            index_expr = None  # 인덱스가 없을 수도 있습니다 (예: array[])

        # 3. Expression 객체 생성
        result_expr = Expression(
            base=base_expr,
            index=index_expr,
            access='index_access',
            context='IndexAccessContext'
        )

        return result_expr

    def visitIndexRangeAccess(self, ctx):
        # 1. 베이스 표현식 방문 (예: array)
        base_expr = self.visitExpression(ctx.expression(0))

        # 2. 시작 인덱스 방문 (선택적)
        start_expr = None
        end_expr = None

        # 자식 노드의 개수
        child_count = ctx.getChildCount()

        # 구조 파악:
        # - ctx.getChild(0): base expression (array)
        # - ctx.getChild(1): '['
        # - 이후의 자식들은 다음과 같은 패턴을 가짐:
        #   - 만약 시작 인덱스가 존재하면 ctx.expression(1)이 있음
        #   - ':' 토큰은 반드시 존재함
        #   - 끝 인덱스가 존재하면 ctx.expression(2)이 있음
        #   - ']' 토큰은 마지막에 위치함

        # 3. 시작 인덱스와 끝 인덱스의 위치 파악
        # 표현식의 개수를 확인합니다.
        expression_count = len(ctx.expression())

        if expression_count == 1:
            # 시작 인덱스와 끝 인덱스가 모두 없는 경우 (예: array[:])
            # 이 경우는 슬라이스의 모든 요소를 선택하는 것을 의미합니다.
            start_expr = None
            end_expr = None
        elif expression_count == 2:
            # 시작 인덱스나 끝 인덱스 중 하나만 존재하는 경우
            # ':'의 위치를 찾아서 구분합니다.
            colon_index = None
            for i in range(child_count):
                if ctx.getChild(i).getText() == ':':
                    colon_index = i
                    break

            if colon_index is not None:
                # ':' 앞의 표현식을 확인하여 시작 인덱스인지 끝 인덱스인지 결정
                if ctx.getChild(colon_index - 1) in ctx.expression():
                    # ':' 앞에 표현식이 있으면 시작 인덱스
                    start_expr = self.visitExpression(ctx.expression(1))
                    end_expr = None
                else:
                    # ':' 앞에 표현식이 없으면 시작 인덱스 없음
                    start_expr = None
                    end_expr = self.visitExpression(ctx.expression(1))
            else:
                # ':'가 없으면 잘못된 구조이므로 예외 처리
                raise SyntaxError("Invalid index range access syntax.")
        elif expression_count == 3:
            # 시작 인덱스와 끝 인덱스가 모두 존재하는 경우
            start_expr = self.visitExpression(ctx.expression(1))
            end_expr = self.visitExpression(ctx.expression(2))
        else:
            # 예상치 못한 경우 예외 처리
            raise SyntaxError("Invalid number of expressions in index range access.")

        # 4. Expression 객체 생성
        result_expr = Expression(
            base=base_expr,
            start_index=start_expr,
            end_index=end_expr,
            operator='[:]',
            context='IndexRangeAccessContext'
        )

        return result_expr

    def visitMemberAccess(self, ctx):
        # 1. 베이스 표현식 방문
        base_expr = self.visitExpression(ctx.expression())

        # 2. 멤버 이름 추출
        if ctx.identifier():
            member_name = ctx.identifier().getText()
        else:
            # 'address' 키워드인 경우
            member_name = ctx.getChild(2).getText()

        # 3. Expression 객체 생성
        result_expr = Expression(
            base=base_expr,
            member=member_name,
            operator='.',
            context='MemberAccessContext'
        )

        return result_expr

    def visitFunctionCallOptions(self, ctx):
        # 1. 베이스 표현식 방문
        base_expr = self.visitExpression(ctx.expression())

        # 2. 옵션 매개변수 처리
        options = {}

        # 옵션 매개변수가 존재하는지 확인
        # 중괄호 안에 있는 자식 노드들을 순회하여 옵션들을 추출합니다.
        # 구조:
        # - '{' 토큰은 ctx.getChild(1)
        # - 옵션 매개변수들은 그 이후의 자식 노드들에 위치
        # - '}' 토큰은 마지막 자식 노드

        child_count = ctx.getChildCount()
        # 옵션 매개변수가 시작되는 인덱스 ( '{' 다음 )
        options_start_index = 2
        # 옵션 매개변수가 끝나는 인덱스 ( '}' 이전 )
        options_end_index = child_count - 1

        i = options_start_index
        while i < options_end_index:
            # 옵션 이름 추출 (identifier)
            option_name = ctx.getChild(i).getText()
            i += 1  # ':' 토큰으로 이동
            if ctx.getChild(i).getText() != ':':
                raise SyntaxError("Expected ':' after option name.")
            i += 1  # 옵션 값 표현식으로 이동
            # 옵션 값 표현식 방문
            option_value_expr = self.visitExpression(ctx.getChild(i))
            i += 1  # 다음 토큰으로 이동

            # 옵션 매개변수 딕셔너리에 추가
            options[option_name] = option_value_expr

            # 다음 옵션이 있는지 확인 (',' 또는 끝)
            if i < options_end_index and ctx.getChild(i).getText() == ',':
                i += 1  # 다음 옵션으로 이동
            else:
                break  # 옵션 매개변수의 끝

        # 3. Expression 객체 생성
        result_expr = Expression(
            function=base_expr,
            options=options,
            operator='{}',
            context='FunctionCallOptionContext'
        )

        return result_expr

    def visitFunctionCall(self, ctx):
        # 1. 함수 표현식 방문
        function_expr = self.visitExpression(ctx.expression())

        # 2. 인자 목록 처리
        arguments, named_arguments = self.process_arguments(ctx.callArgumentList())

        # 3. Expression 객체 생성
        result_expr = Expression(
            function=function_expr,
            arguments=arguments,
            named_arguments=named_arguments,
            operator='()',
            context='FunctionCallContext'
        )

        return result_expr

    def visitPayableFunctionCall(self, ctx):
        # 1. 'payable' 키워드 처리
        payable_keyword = ctx.PayableKeyword().getText()
        function_expr = Expression(identifier=payable_keyword)

        # 2. 인자 목록 처리
        arguments, named_arguments = self.process_arguments(ctx.callArgumentList())

        # 3. Expression 객체 생성
        result_expr = Expression(
            function=function_expr,
            arguments=arguments,
            named_arguments=named_arguments,
            operator='()',
            context='PayableFunctionCallContext'
        )

        return result_expr

    def process_arguments(self, call_args_ctx):
        arguments = []
        named_arguments = {}

        if call_args_ctx:
            child_count = call_args_ctx.getChildCount()
            if child_count < 2:
                raise SyntaxError("Invalid function call syntax.")

            if child_count == 2:
                # This means we have '()' with no arguments
                pass  # No arguments
            else:
                # Check if the first token after '(' is '{'
                if call_args_ctx.getChild(1).getText() == '{':
                    # Handle named arguments
                    i = 2  # Start after '{'
                    while i < child_count - 2:
                        arg_name = call_args_ctx.getChild(i).getText()
                        i += 1  # Move to ':'
                        if call_args_ctx.getChild(i).getText() != ':':
                            raise SyntaxError("Expected ':' after argument name.")
                        i += 1  # Move to expression
                        arg_expr_ctx = call_args_ctx.getChild(i)
                        arg_expr = self.visitExpression(arg_expr_ctx)
                        named_arguments[arg_name] = arg_expr
                        i += 1  # Move to next token
                        if i < child_count - 1 and call_args_ctx.getChild(i).getText() == ',':
                            i += 1  # Move to next argument
                        elif call_args_ctx.getChild(i).getText() == '}':
                            i += 1  # Skip '}'
                            break
                        else:
                            raise SyntaxError("Expected ',' or '}' in named arguments.")
                else:
                    # Handle positional arguments
                    i = 1  # Start after '('
                    while i < child_count - 1:
                        arg_ctx = call_args_ctx.getChild(i)
                        if arg_ctx.getText() == ',':
                            i += 1
                            continue
                        arg_expr = self.visitExpression(arg_ctx)
                        arguments.append(arg_expr)
                        i += 1
        else:
            pass  # No arguments (shouldn't occur with the adjusted grammar)

        return arguments if arguments else None, named_arguments if named_arguments else None

    # Visit a parse tree produced by SolidityParser#IdentifierExp.
    def visitIdentifierExp(self, ctx:SolidityParser.IdentifierExpContext):
        # 식별자 이름 추출
        identifier_name = ctx.getText()
        result_expr = Expression(identifier=identifier_name,
                                 context='IdentifierExpContext')
        return result_expr

    # Visit a parse tree produced by SolidityParser#LiteralExp.
    def visitLiteralExp(self, ctx:SolidityParser.LiteralExpContext):
        # 리터럴 값 추출
        literal_value = ctx.getText()
        result_expr = Expression(literal=literal_value,
                                 context='LiteralExpContext')

        # 리터럴 값이 숫자인 경우 int 또는 uint로 설정
        if literal_value.isdigit() or (literal_value.startswith('0x') or literal_value.startswith('0X')):
            # 숫자 리터럴 처리: 10진수, 16진수 구분
            result_expr.expr_type = 'uint' if literal_value.isdigit() else 'int'
            result_expr.type_length = 256  # 기본적으로 256비트로 가정

        # Boolean 리터럴인 경우
        elif literal_value.lower() == 'true' or literal_value.lower() == 'false':
            result_expr.expr_type = 'bool'

        # 그 외 문자열 리터럴 등
        else:
            result_expr.expr_type = 'string'  # 문자열 또는 기타 리터럴 값

        return result_expr

    # Visit a parse tree produced by SolidityParser#ConditionalExp.
    def visitConditionalExp(self, ctx:SolidityParser.ConditionalExpContext):
        # 조건식 방문
        condition_expr = self.visitExpression(ctx.expression(0))

        # 참일 때의 표현식 방문
        true_expr = self.visitExpression(ctx.expression(1))

        # 거짓일 때의 표현식 방문
        false_expr = self.visitExpression(ctx.expression(2))

        # Expression 객체 생성
        result_expr = Expression(
            condition=condition_expr,
            true_expr=true_expr,
            false_expr=false_expr,
            operator='?:',
            context='ConditionalExpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#Exponentiation.
    def visitExponentiation(self, ctx:SolidityParser.ExponentiationContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정
        operator = '**'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='ExponentiationContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#LiteralSubDenomination.
    def visitLiteralSubDenomination(self, ctx:SolidityParser.LiteralSubDenominationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#TupleExp.
    def visitTupleExp(self, ctx:SolidityParser.TupleExpContext):
        # 요소들 추출
        elements = []
        expression_list = ctx.expression()
        for expr_ctx in expression_list:
            element_expr = self.visitExpression(expr_ctx)
            elements.append(element_expr)

        # Expression 객체 생성
        result_expr = Expression(
            elements=elements,
            operator='tuple',
            context='TupleExpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#Assignment.
    def visitAssignment(self, ctx:SolidityParser.AssignmentContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='AssignmentOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#TypeConversion.
    def visitTypeConversion(self, ctx:SolidityParser.TypeConversionContext):
        # 1. 타입 이름 추출
        type_name = ctx.elementaryTypeName().getText()

        # 2. 식별자 또는 표현식 추출
        if ctx.expression():
            # 표현식인 경우
            expr = self.visitExpression(ctx.expression())
        elif ctx.identifier():
            # 식별자인 경우
            identifier = ctx.identifier().getText()
            expr = Expression(identifier=identifier)
        else:
            raise SyntaxError("Expected expression or identifier in type conversion.")

        # 3. 타입 변환 Expression 객체 생성
        result_expr = Expression(
            type_name=type_name,
            expression=expr,
            operator='type_conversion',
            context='TypeConversionContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#UnaryPrefixOp.
    def visitUnaryPrefixOp(self, ctx:SolidityParser.UnaryPrefixOpContext):
        operator = ctx.getChild(0).getText()
        expression = self.visitExpression(ctx.expression())
        result_expr = Expression(
            operator=operator,
            expression=expression,
            is_postfix=False,
            context='UnaryPrefixOpContext'
        )
        return result_expr

    # Visit a parse tree produced by SolidityParser#BitXorOp.
    def visitBitXorOp(self, ctx:SolidityParser.BitXorOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정 ('^')
        operator = '^'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='BitXorOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#AdditiveOp.
    def visitAdditiveOp(self, ctx:SolidityParser.AdditiveOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출 ('+', '-')
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='AdditiveOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#NewExp.
    def visitNewExp(self, ctx:SolidityParser.NewExpContext):
        # 타입 이름 방문
        type_name = self.visitTypeName(ctx.typeName())

        # Expression 객체 생성
        result_expr = Expression(
            operator='new',
            type_name=type_name,
            context='NewExpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#BitAndOp.
    def visitBitAndOp(self, ctx:SolidityParser.BitAndOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정 ('&')
        operator = '&'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='BitAndOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#BitOrOp.
    def visitBitOrOp(self, ctx:SolidityParser.BitOrOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정 ('|')
        operator = '|'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='BitOrOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#UnarySuffixOp.
    def visitUnarySuffixOp(self, ctx:SolidityParser.UnarySuffixOpContext):
        # 피연산자 표현식 방문
        expr = self.visitExpression(ctx.expression())

        # 연산자 추출
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            operator=operator,
            expression=expr,
            is_postfix=True,  # 후위 연산자임을 표시
            context='UnarySuffixOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#MultiplicativeOp.
    def visitMultiplicativeOp(self, ctx:SolidityParser.MultiplicativeOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출 ('*', '/', '%')
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='MultiplicativeOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#EqualityOp.
    def visitEqualityOp(self, ctx:SolidityParser.EqualityOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출 ('==', '!=')
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='EqualityOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#AndOperation.
    def visitAndOperation(self, ctx:SolidityParser.AndOperationContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정 ('&&')
        operator = '&&'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='AndOperationOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#RelationalOp.
    def visitRelationalOp(self, ctx:SolidityParser.RelationalOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출 ('<', '>', '<=', '>=')
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='RelationalOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#OrOperation.
    def visitOrOperation(self, ctx:SolidityParser.OrOperationContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 설정 ('||')
        operator = '||'

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='OrOperationContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#ShiftOp.
    def visitShiftOp(self, ctx:SolidityParser.ShiftOpContext):
        # 좌측 표현식 방문
        left_expr = self.visitExpression(ctx.expression(0))

        # 우측 표현식 방문
        right_expr = self.visitExpression(ctx.expression(1))

        # 연산자 추출 ('<<', '>>', '>>>')
        operator = ctx.getChild(1).getText()

        # Expression 객체 생성
        result_expr = Expression(
            left=left_expr,
            operator=operator,
            right=right_expr,
            context='ShiftOpContext'
        )

        return result_expr

    # Visit a parse tree produced by SolidityParser#TypeNameExp.
    def visitTypeNameExp(self, ctx:SolidityParser.TypeNameExpContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#InlineArrayExp.
    def visitInlineArrayExp(self, ctx:SolidityParser.InlineArrayExpContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#literal.
    def visitLiteral(self, ctx:SolidityParser.LiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#literalWithSubDenomination.
    def visitLiteralWithSubDenomination(self, ctx:SolidityParser.LiteralWithSubDenominationContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#tupleExpression.
    def visitTupleExpression(self, ctx:SolidityParser.TupleExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#numberLiteral.
    def visitNumberLiteral(self, ctx:SolidityParser.NumberLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#identifier.
    def visitIdentifier(self, ctx:SolidityParser.IdentifierContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#userDefinedValueTypeDefinition.
    def visitUserDefinedValueTypeDefinition(self, ctx:SolidityParser.UserDefinedValueTypeDefinitionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#booleanLiteral.
    def visitBooleanLiteral(self, ctx:SolidityParser.BooleanLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#hexStringLiteral.
    def visitHexStringLiteral(self, ctx:SolidityParser.HexStringLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#unicodeStringLiteral.
    def visitUnicodeStringLiteral(self, ctx:SolidityParser.UnicodeStringLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#stringLiteral.
    def visitStringLiteral(self, ctx:SolidityParser.StringLiteralContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by SolidityParser#overrideSpecifier.
    def visitOverrideSpecifier(self, ctx:SolidityParser.OverrideSpecifierContext):
        return self.visitChildren(ctx)

    def evaluate_expression(self, expr):
        # 1. LiteralExp 처리
        if isinstance(expr, SolidityParser.LiteralExpContext):
            return self.evaluate_literal_expression(expr)

        # 2. IndexAccess 처리
        elif expr.expression_type == 'index_access':
            base_var = self.evaluate_expression(expr.base)
            index_value = self.evaluate_expression(expr.index)

            if isinstance(base_var, ArrayVariable):
                index = index_value.min_value  # 인덱스 값 (Interval의 최소값)
                if 0 <= index < len(base_var.elements):
                    return base_var.elements[index].value
                else:
                    raise IndexError(f"Array index out of bounds: {index}")
            elif isinstance(base_var, MappingVariable):
                if index_value not in base_var.elements:
                    # Mapping에 해당 키가 없을 경우 기본값 생성
                    base_var.elements[index_value] = self.create_default_value(base_var.typeInfo.mappingValueType)
                return base_var.elements[index_value].value
            else:
                raise TypeError(f"Index access on non-array variable: {base_var}")

        # 다른 표현식의 경우 처리 계속
        # 여기에 다른 expression 규칙을 추가할 수 있음

    def create_default_value(self, value_type):
        """
        주어진 값 타입에 따라 기본 값을 생성하는 함수 (예: 기본 Interval 등).
        """
        if value_type.typeCategory == 'elementary':
            if value_type.elementaryTypeName.startswith('int'):
                type_length = self.get_elementary_type_length(value_type.elementaryTypeName, default_length=256)
                return IntegerInterval(float('-inf'), float('inf'), type_length)
            elif value_type.elementaryTypeName.startswith('uint'):
                type_length = self.get_elementary_type_length(value_type.elementaryTypeName, default_length=256)
                return UnsignedIntegerInterval(0, float('inf'), type_length)
            elif value_type.elementaryTypeName == 'bool':
                return BoolInterval(is_true=False, is_false=True)
        elif value_type.typeCategory == 'mapping':
            return MappingVariable()  # 기본 Mapping 객체 생성
        elif value_type.typeCategory == 'array':
            return ArrayVariable()  # 기본 Array 객체 생성
        elif value_type.typeCategory == 'struct':
            return StructVariable()  # 기본 Struct 객체 생성
        else:
            raise ValueError(f"Unsupported value type: {value_type.typeCategory}")

    def get_elementary_type_length(self, elementary_type_name, default_length=256):
        """
        주어진 elementary 타입 이름에서 비트 길이를 추출합니다.
        기본적으로 길이가 명시되지 않으면 default_length를 사용합니다.
        """
        if elementary_type_name == 'int' or elementary_type_name == 'uint':
            return default_length
        else:
            try:
                # 'int256', 'uint128' 등의 경우 뒤에 숫자가 붙어있는지 확인
                return int(elementary_type_name[3:])  # 예: 'int256' -> 256
            except ValueError:
                # 만약 숫자가 없다면 기본값 사용
                return default_length

    def evaluate_literal_expression(self, expr):
        """
        literal 표현식 (숫자, 문자열, boolean 등)을 처리하는 함수.
        LiteralExpContext에서 리터럴 값을 분석하여 처리합니다.
        """
        literal_text = expr.getText()  # 리터럴 텍스트 가져오기

        # 숫자 리터럴인지 확인
        if literal_text.isdigit():
            return self.evaluate_number_literal(literal_text)

        # 불리언 리터럴인지 확인
        elif literal_text == 'true' or literal_text == 'false':
            return self.evaluate_boolean_literal(literal_text)

        # 기타 리터럴 타입 (16진수 문자열, 유니코드 등)
        elif literal_text.startswith("0x"):
            return self.evaluate_hex_string_literal(literal_text)

        elif literal_text.startswith('"') and literal_text.endswith('"'):
            return self.evaluate_string_literal(literal_text)

        else:
            raise ValueError(f"Unsupported literal type: {literal_text}")

    def evaluate_number_literal(self, literal_text):
        """
        숫자 리터럴 처리
        """
        return int(literal_text)

    def evaluate_boolean_literal(self, literal_text):
        """
        boolean 리터럴 처리
        """
        if literal_text == 'true':
            return True
        elif literal_text == 'false':
            return False

    def evaluate_hex_string_literal(self, literal_text):
        """
        16진수 리터럴 처리
        """
        return int(literal_text, 16)

    def evaluate_string_literal(self, literal_text):
        """
        문자열 리터럴 처리
        """
        return literal_text.strip('"')  # 따옴표 제거 후 반환


