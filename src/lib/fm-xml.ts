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
