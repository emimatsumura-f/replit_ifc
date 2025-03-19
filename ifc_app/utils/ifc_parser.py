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

        # BeamとColumnの要素を取得
        beams = ifc_file.by_type('IfcBeam')
        columns = ifc_file.by_type('IfcColumn')

        # Beamの情報を処理
        for beam in beams:
            try:
                properties = {
                    "type": "IfcBeam",
                    "name": beam.Name if hasattr(beam, 'Name') else "未定義",
                    "description": beam.Description if hasattr(beam, 'Description') else "未定義",
                    "size": extract_profile_information(beam),
                    "weight": get_weight(beam),
                    "length": get_length(beam)
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Beam {beam.id()} の処理中にエラーが発生: {str(e)}")
                continue

        # Columnの情報を処理
        for column in columns:
            try:
                properties = {
                    "type": "IfcColumn",
                    "name": column.Name if hasattr(column, 'Name') else "未定義",
                    "description": column.Description if hasattr(column, 'Description') else "未定義",
                    "size": extract_profile_information(column),
                    "weight": get_weight(column),
                    "length": get_length(column)
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Column {column.id()} の処理中にエラーが発生: {str(e)}")
                continue

        return elements

    except Exception as e:
        logger.error(f"IFCファイルの処理中にエラーが発生: {str(e)}")
        raise

def extract_profile_information(element):
    """部材のプロファイル情報を抽出"""
    try:
        # まず、Description属性をチェック
        if hasattr(element, 'Description') and element.Description:
            return element.Description

        # PropertySetから情報を取得
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        # 断面性能に関連するpropertyを検索
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
        for rel in element.IsDefinedBy:
            if rel.is_a('IfcRelDefinesByProperties'):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a('IfcPropertySet'):
                    for prop in property_set.HasProperties:
                        if prop.Name.lower() in ['weight', 'mass']:
                            if hasattr(prop, 'NominalValue'):
                                return prop.NominalValue.wrappedValue
        return "未定義"
    except:
        return "未定義"

def get_length(element):
    """部材の長さ情報を抽出"""
    try:
        for rel in element.IsDefinedBy:
            if rel.is_a('IfcRelDefinesByProperties'):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a('IfcElementQuantity'):
                    for q in property_set.Quantities:
                        if q.is_a('IfcQuantityLength'):
                            return q.LengthValue
        return "未定義"
    except:
        return "未定義"
