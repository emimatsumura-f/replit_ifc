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
                    "size": get_size(element),  # サイズ情報
                    "weight": get_weight(element),  # 重量情報
                    "length": get_length(element),  # 長さ情報
                    "quantity": 1  # デフォルトの数量
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"部材 {element.id()} の処理中にエラーが発生: {str(e)}")
                continue

        # 同じ種類の部材をグループ化して数量を集計
        grouped_elements = {}
        for element in elements:
            key = (element["type"], element["size"])
            if key in grouped_elements:
                grouped_elements[key]["quantity"] += 1
            else:
                grouped_elements[key] = element

        return list(grouped_elements.values())

    except Exception as e:
        logger.error(f"IFCファイルの処理中にエラーが発生: {str(e)}")
        raise

def get_size(element):
    """部材のサイズ情報を抽出"""
    try:
        # プロパティセットから情報を取得
        psets = element.IsDefinedBy
        for definition in psets:
            if definition.is_a("IfcRelDefinesByProperties"):
                props = definition.RelatingPropertyDefinition
                if props.is_a("IfcPropertySet"):
                    for prop in props.HasProperties:
                        if "Section" in prop.Name or "Profile" in prop.Name:
                            return prop.NominalValue.wrappedValue
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