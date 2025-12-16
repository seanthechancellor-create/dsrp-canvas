/**
 * DSRPIcons - SVG icon components for DSRP patterns
 *
 * D (Distinctions): Split icon - identity/other separation
 * S (Systems): Nested boxes - parts within whole
 * R (Relationships): Connected nodes - action/reaction links
 * P (Perspectives): Eye icon - point/view
 */

import { CSSProperties } from 'react'

interface IconProps {
  size?: number
  color?: string
  className?: string
  style?: CSSProperties
}

// DSRP Pattern colors
export const DSRP_COLORS = {
  D: '#1976D2',
  S: '#388E3C',
  R: '#F57C00',
  P: '#7B1FA2',
} as const

export const DSRP_NAMES = {
  D: 'Distinctions',
  S: 'Systems',
  R: 'Relationships',
  P: 'Perspectives',
} as const

export const DSRP_ELEMENTS = {
  D: ['identity', 'other'],
  S: ['part', 'whole'],
  R: ['action', 'reaction'],
  P: ['point', 'view'],
} as const

// D - Distinctions: Split/divide icon showing identity vs other
export function DistinctionIcon({ size = 24, color = DSRP_COLORS.D, className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={style}
    >
      {/* Left half - identity */}
      <rect x="3" y="4" width="7" height="16" rx="2" fill={color} opacity="0.9" />
      {/* Right half - other */}
      <rect x="14" y="4" width="7" height="16" rx="2" fill={color} opacity="0.4" />
      {/* Dividing line */}
      <line x1="12" y1="2" x2="12" y2="22" stroke={color} strokeWidth="2" strokeDasharray="2 2" />
    </svg>
  )
}

// S - Systems: Nested boxes showing parts within whole
export function SystemIcon({ size = 24, color = DSRP_COLORS.S, className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={style}
    >
      {/* Outer box - whole */}
      <rect x="2" y="2" width="20" height="20" rx="3" stroke={color} strokeWidth="2" fill="none" />
      {/* Inner boxes - parts */}
      <rect x="5" y="5" width="5" height="5" rx="1" fill={color} opacity="0.7" />
      <rect x="14" y="5" width="5" height="5" rx="1" fill={color} opacity="0.7" />
      <rect x="5" y="14" width="5" height="5" rx="1" fill={color} opacity="0.7" />
      <rect x="14" y="14" width="5" height="5" rx="1" fill={color} opacity="0.7" />
    </svg>
  )
}

// R - Relationships: Connected nodes showing action/reaction
export function RelationshipIcon({ size = 24, color = DSRP_COLORS.R, className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={style}
    >
      {/* Left node - action */}
      <circle cx="6" cy="12" r="4" fill={color} />
      {/* Right node - reaction */}
      <circle cx="18" cy="12" r="4" fill={color} />
      {/* Bidirectional arrow */}
      <line x1="10" y1="12" x2="14" y2="12" stroke={color} strokeWidth="2" />
      {/* Arrow heads */}
      <polyline points="11,9 14,12 11,15" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="13,9 10,12 13,15" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// P - Perspectives: Eye icon showing point of view
export function PerspectiveIcon({ size = 24, color = DSRP_COLORS.P, className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={style}
    >
      {/* Eye outline */}
      <path
        d="M12 5C7 5 2.73 8.11 1 12.5C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12.5C21.27 8.11 17 5 12 5Z"
        stroke={color}
        strokeWidth="2"
        fill="none"
      />
      {/* Iris */}
      <circle cx="12" cy="12.5" r="4" fill={color} opacity="0.3" />
      {/* Pupil - the point */}
      <circle cx="12" cy="12.5" r="2" fill={color} />
    </svg>
  )
}

// Combined icon selector
export type DSRPPattern = 'D' | 'S' | 'R' | 'P'

interface DSRPIconProps extends IconProps {
  pattern: DSRPPattern
}

export function DSRPIcon({ pattern, size = 24, color, className, style }: DSRPIconProps) {
  const iconColor = color || DSRP_COLORS[pattern]

  switch (pattern) {
    case 'D':
      return <DistinctionIcon size={size} color={iconColor} className={className} style={style} />
    case 'S':
      return <SystemIcon size={size} color={iconColor} className={className} style={style} />
    case 'R':
      return <RelationshipIcon size={size} color={iconColor} className={className} style={style} />
    case 'P':
      return <PerspectiveIcon size={size} color={iconColor} className={className} style={style} />
  }
}

// Pattern data for iteration
export const DSRP_PATTERNS = [
  { id: 'D' as const, name: 'Distinctions', elements: ['identity', 'other'], color: DSRP_COLORS.D, Icon: DistinctionIcon },
  { id: 'S' as const, name: 'Systems', elements: ['part', 'whole'], color: DSRP_COLORS.S, Icon: SystemIcon },
  { id: 'R' as const, name: 'Relationships', elements: ['action', 'reaction'], color: DSRP_COLORS.R, Icon: RelationshipIcon },
  { id: 'P' as const, name: 'Perspectives', elements: ['point', 'view'], color: DSRP_COLORS.P, Icon: PerspectiveIcon },
] as const
