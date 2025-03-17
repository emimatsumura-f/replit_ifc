import ifcopenshell
import logging

logger = logging.getLogger(__name__)

def process_ifc_file(filepath):
    """
    IFCファイルを処理して部材情報を抽出する
    """
    try:
        ifc_file = ifcopenshell.open(filepath)
        elements = []

        # 建築部材の処理
        for element in ifc_file.by_type("IfcBuildingElement"):
            try:
                # プロパティの抽出
                properties = {
                    "type": element.is_a(),  # 部材の種類
                    "size": get_section_profile(element),  # 断面性能情報
                    "weight": get_weight(element),  # 重量情報
                    "length": get_length(element),  # 長さ情報
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"部材 {element.id()} の処理中にエラーが発生: {str(e)}")
                continue

        return elements

    except Exception as e:
        logger.error(f"IFCファイルの処理中にエラーが発生: {str(e)}")
        raise

def get_section_profile(element):
    """部材の断面性能情報を抽出"""
    try:
        # 断面形状の情報を取得
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        # 断面性能に関連する property を検索
                        if any(keyword in prop.Name.lower() for keyword in ["section", "profile", "size"]):
                            if hasattr(prop, "NominalValue"):
                                return prop.NominalValue.wrappedValue

        # 材料プロファイルから情報を取得
        for rel in element.HasAssociations:
            if rel.is_a("IfcRelAssociatesMaterial"):
                material = rel.RelatingMaterial
                if material.is_a("IfcMaterialProfileSet"):
                    for profile in material.MaterialProfiles:
                        if profile.Profile:
                            return profile.Profile.ProfileName

        return "未定義"
    except:
        return "未定義"

def get_weight(element):
    """部材の重量情報を抽出"""
    try:
        # 材料プロパティから情報を取得
        material = element.HasAssociations
        for association in material:
            if association.is_a("IfcRelAssociatesMaterial"):
                material_select = association.RelatingMaterial
                if hasattr(material_select, "MaterialProperties"):
                    for props in material_select.MaterialProperties:
                        if props.is_a("IfcMechanicalMaterialProperties"):
                            return props.SpecificGravity
        return "未定義"
    except:
        return "未定義"

def get_length(element):
    """部材の長さ情報を抽出"""
    try:
        # 数量セットから情報を取得
        quantities = element.IsDefinedBy
        for definition in quantities:
            if definition.is_a("IfcRelDefinesByProperties"):
                props = definition.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for quantity in props.Quantities:
                        if quantity.is_a("IfcQuantityLength"):
                            return quantity.LengthValue
        return "未定義"
    except:
        return "未定義"