export type FMFieldType = 'Text' | 'Number' | 'Date' | 'Time' | 'Timestamp' | 'Container' | 'Calculation' | 'Summary';

export interface FMField {
  name: string;
  type: FMFieldType;
  formula?: string;
  global?: boolean;
}

export interface FMTable {
  name: string;
  fields: FMField[];
}

/**
 * Generates XML for multiple fields that can be pasted into FileMaker's Manage Database > Fields tab.
 */
export function generateFieldsXML(fields: FMField[]): string {
  let xml = '<FMPXmlSnippet type="FMField">\n';

  fields.forEach((field) => {
    // id="0" allows FileMaker to auto-assign IDs
    xml += `  <Field datatype="${field.type}" id="0" name="${field.name}">\n`;

    if (field.global) {
      xml += '    <Storage global="True" maxRepeat="1" />\n';
    } else {
      xml += '    <Storage autoIndex="True" maxRepeat="1" onload="True" recalculate="True" />\n';
    }

    if (field.type === 'Calculation' && field.formula) {
      xml += `    <Calculation>\n      <Calculation formula="${escapeXml(field.formula)}" />\n    </Calculation>\n`;
    }

    xml += '  </Field>\n';
  });

  xml += '</FMPXmlSnippet>';
  return xml;
}

/**
 * Generates XML for a table that can be pasted into FileMaker's Manage Database > Tables tab.
 */
export function generateTableXML(table: FMTable): string {
  let xml = '<FMPXmlSnippet type="FMTable">\n';
  xml += `  <Table name="${table.name}" id="0">\n`;

  table.fields.forEach((field) => {
    xml += `    <Field datatype="${field.type}" id="0" name="${field.name}">\n`;
    xml += '      <Storage autoIndex="True" maxRepeat="1" onload="True" recalculate="True" />\n';
    xml += '    </Field>\n';
  });

  xml += '  </Table>\n';
  xml += '</FMPXmlSnippet>';
  return xml;
}

export interface FMLayoutStyle {
  primaryColor?: string;
  accentColor?: string;
  theme?: 'dark' | 'light' | 'glass';
}

export interface FMLayoutElement {
  field: string;
  label: string;
  grid: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
}

export interface FMLayout {
  name: string;
  table: string;
  type: 'dashboard' | 'form' | 'list';
  style: FMLayoutStyle;
  elements: FMLayoutElement[];
}

/**
 * Generates XML for layout objects (fields and labels) that can be pasted into FileMaker's Layout Mode.
 */
export function generateLayoutXML(layout: FMLayout): string {
  let xml = '<FMPXmlSnippet type="LayoutObjectList">\n';

  const GRID_SIZE_X = 80; // 1 unit = 80pt
  const GRID_SIZE_Y = 60; // 1 unit = 60pt
  const MARGIN = 20;

  layout.elements.forEach((el, index) => {
    const left = el.grid.x * GRID_SIZE_X + MARGIN;
    const top = el.grid.y * GRID_SIZE_Y + MARGIN;
    const width = el.grid.w * GRID_SIZE_X - 10;
    const height = el.grid.h * GRID_SIZE_Y - 10;

    // Label Object
    xml += `  <LayoutObject type="Text">\n`;
    xml += `    <Bounds top="${top}" left="${left}" bottom="${top + 20}" right="${left + width / 3}" />\n`;
    xml += `    <TextContent>${escapeXml(el.label)}</TextContent>\n`;
    xml += `  </LayoutObject>\n`;

    // Field Object
    const fieldLeft = left + width / 3 + 10;
    xml += `  <LayoutObject type="Field">\n`;
    xml += `    <Bounds top="${top}" left="${fieldLeft}" bottom="${top + height}" right="${left + width}" />\n`;
    xml += `    <FieldReference name="${el.field}" table="${layout.table}" />\n`;
    xml += `  </LayoutObject>\n`;
  });

  xml += '</FMPXmlSnippet>';
  return xml;
}

function escapeXml(unsafe: string): string {
  return unsafe.replace(/[<>&"']/g, (c) => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '"': return '&quot;';
      case "'": return '&apos;';
      default: return c;
    }
  });
}
