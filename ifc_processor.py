import ifcopenshell
import logging

logger = logging.getLogger(__name__)

def process_ifc_file(filepath):
    """
    Process IFC file and extract element information
    """
    try:
        ifc_file = ifcopenshell.open(filepath)
        elements = []

        # Process building elements
        for element in ifc_file.by_type("IfcBuildingElement"):
            try:
                # Extract properties
                properties = {
                    "type": element.is_a(),
                    "size": get_size(element),
                    "weight": get_weight(element),
                    "length": get_length(element),
                    "quantity": 1  # Default quantity
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Error processing element {element.id()}: {str(e)}")
                continue

        # Group similar elements and sum quantities
        grouped_elements = {}
        for element in elements:
            key = (element["type"], element["size"])
            if key in grouped_elements:
                grouped_elements[key]["quantity"] += 1
            else:
                grouped_elements[key] = element

        return list(grouped_elements.values())

    except Exception as e:
        logger.error(f"Error processing IFC file: {str(e)}")
        raise

def get_size(element):
    """Extract size information from element"""
    try:
        # Try to get property sets
        psets = element.IsDefinedBy
        for definition in psets:
            if definition.is_a("IfcRelDefinesByProperties"):
                props = definition.RelatingPropertyDefinition
                if props.is_a("IfcPropertySet"):
                    for prop in props.HasProperties:
                        if "Section" in prop.Name or "Profile" in prop.Name:
                            return prop.NominalValue.wrappedValue
        return "N/A"
    except:
        return "N/A"

def get_weight(element):
    """Extract weight information from element"""
    try:
        # Try to get material properties
        material = element.HasAssociations
        for association in material:
            if association.is_a("IfcRelAssociatesMaterial"):
                material_select = association.RelatingMaterial
                if hasattr(material_select, "MaterialProperties"):
                    for props in material_select.MaterialProperties:
                        if props.is_a("IfcMechanicalMaterialProperties"):
                            return props.SpecificGravity
        return "N/A"
    except:
        return "N/A"

def get_length(element):
    """Extract length information from element"""
    try:
        # Try to get quantity sets
        quantities = element.IsDefinedBy
        for definition in quantities:
            if definition.is_a("IfcRelDefinesByProperties"):
                props = definition.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for quantity in props.Quantities:
                        if quantity.is_a("IfcQuantityLength"):
                            return quantity.LengthValue
        return "N/A"
    except:
        return "N/A"
