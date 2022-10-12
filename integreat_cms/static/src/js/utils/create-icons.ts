import { icons, createElement } from "lucide";

// This function renders all <i icon-name="..."> children of `root`
export function create_icons_at(root: HTMLElement) {
  const elementsToReplace = root.querySelectorAll('[icon-name]');
  Array.from(elementsToReplace).forEach(element => replace_element(element as HTMLElement, 'icon-name', { class: ['inline-block'] }));
}

// Most of this is taken from https://github.com/lucide-icons/lucide/tree/main/packages/lucide/src

function replace_element(element: HTMLElement, nameAttr: string, attrs: object) {
  const iconName = element.getAttribute(nameAttr);
  const ComponentName = toPascalCase(iconName);

  const iconNode = icons[ComponentName];

  if (!iconNode) {
    return console.warn(
      `${element.outerHTML} icon name was not found in the provided icons object.`,
    );
  }

  const elementAttrs = getAttrs(element);
  const [tag, iconAttributes, children] = iconNode;

  const iconAttrs = {
    ...iconAttributes,
    'icon-name': iconName,
    ...attrs,
    ...elementAttrs,
  };

  const classNames = combineClassNames(['lucide', `lucide-${iconName}`, elementAttrs, attrs]);

  if (classNames) {
    iconAttrs.class = classNames;
  }

  const svgElement = createElement([tag, iconAttrs, children]);

  return element.parentNode.replaceChild(svgElement, element);

}

export const getAttrs = (element: HTMLElement) =>
  Array.from(element.attributes).reduce((attrs: any, attr) => {
    attrs[attr.name] = attr.value;
    return attrs;
  }, {});

export const combineClassNames = (arrayOfClassnames: Array<string>) => {
  const classNameArray = arrayOfClassnames.flatMap(getClassNames);

  return classNameArray
    .map(classItem => classItem.trim())
    .filter(Boolean)
    .filter((value, index, self) => self.indexOf(value) === index)
    .join(' ');
};

export const getClassNames = (attrs: any) => {
  if (typeof attrs === 'string') return attrs;
  if (!attrs || !attrs.class) return '';
  if (attrs.class && typeof attrs.class === 'string') {
    return attrs.class.split(' ');
  }
  if (attrs.class && Array.isArray(attrs.class)) {
    return attrs.class;
  }
  return '';
};

const toPascalCase = (str: string) =>
  str.replace(/(\w)(\w*)(_|-|\s*)/g, (g0, g1, g2) => g1.toUpperCase() + g2.toLowerCase());